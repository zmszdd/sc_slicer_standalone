#!/usr/bin/env python3
"""
Fallback flattener for Code4rena projects whose submissions API is forbidden.

This is intentionally separate from code4rena_flatten_pipeline.py. The main
pipeline flattens exact linesOfCode URLs from Code4rena findings. This fallback
uses the public audit source repository when finding-level data is inaccessible:
it prefers Solidity paths mentioned in README/scope files, then falls back to a
filtered repository scan.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urlparse


DEFAULT_EXCLUDED_DIRS = {
    ".git",
    "artifacts",
    "broadcast",
    "cache",
    "coverage",
    "dist",
    "docs",
    "node_modules",
    "lib",
    "libs",
    "out",
    "pkg",
    "target",
    "typechain",
    "typechain-types",
    "vendor",
}
DEFAULT_TEST_DIRS = {
    "__tests__",
    "bench",
    "benches",
    "demo",
    "demos",
    "example",
    "examples",
    "fixture",
    "fixtures",
    "mock",
    "mocks",
    "script",
    "scripts",
    "spec",
    "specs",
    "test",
    "tests",
}
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "c4_pipeline_output"


@dataclass
class FallbackRecord:
    project_id: str
    title: str
    repo: str
    relative_path: str
    source_path: str
    original_source_path: str
    raw_flatten_path: str
    sorted_flatten_path: str
    status: str
    error: str = ""
    source_reason: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Flatten public source repos for 403 Code4rena projects.")
    parser.add_argument("--access-csv", type=Path, default=DEFAULT_OUTPUT_DIR / "_batch_logs" / "failed_403_repo_access.csv")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_OUTPUT_DIR / "_fallback_source_repos")
    parser.add_argument("--fix-script", type=Path, default=DEFAULT_OUTPUT_DIR / "_tools" / "identity_fix_flatten_order.py")
    parser.add_argument("--forge-bin", default="forge")
    parser.add_argument("--python-bin", default=sys.executable)
    parser.add_argument("--jobs", type=int, default=2, help="Parallel projects.")
    parser.add_argument("--command-timeout", type=int, default=180)
    parser.add_argument("--per-project-limit", type=int, default=0, help="0 means no explicit limit.")
    parser.add_argument("--start-at", type=int, default=1)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--include-tests", action="store_true")
    parser.add_argument("--submodules", action="store_true", help="Initialize git submodules before flattening.")
    return parser.parse_args()


def safe_name(value: str, max_len: int = 140) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value or "").strip("._-")
    return value[:max_len] or "item"


def run_command(cmd: list[str], cwd: Path | None = None, timeout_s: int = 180) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(cmd, 124, stdout=exc.stdout or "", stderr=f"Timed out after {timeout_s}s")


def read_rows(access_csv: Path, start_at: int, limit: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with access_csv.open(newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("repo_access") != "accessible":
                continue
            row_no = int(row["row"])
            if row_no < start_at:
                continue
            rows.append(row)
            if limit and len(rows) >= limit:
                break
    return rows


def clone_or_update(repo_url: str, checkout: Path, timeout_s: int) -> tuple[bool, str]:
    checkout.parent.mkdir(parents=True, exist_ok=True)
    git_url = repo_url if repo_url.endswith(".git") else f"{repo_url}.git"
    if (checkout / ".git").exists():
        proc = run_command(["git", "fetch", "--depth", "1", "origin"], cwd=checkout, timeout_s=timeout_s)
        if proc.returncode != 0:
            head_proc = run_command(["git", "rev-parse", "--verify", "HEAD"], cwd=checkout, timeout_s=timeout_s)
            if head_proc.returncode == 0:
                return True, f"fetch failed; reused existing checkout: {(proc.stderr or proc.stdout).strip()}"
            return False, (proc.stderr or proc.stdout).strip()
        proc = run_command(["git", "reset", "--hard", "origin/HEAD"], cwd=checkout, timeout_s=timeout_s)
        if proc.returncode != 0:
            proc = run_command(["git", "reset", "--hard", "origin/main"], cwd=checkout, timeout_s=timeout_s)
        if proc.returncode != 0:
            head_proc = run_command(["git", "rev-parse", "--verify", "HEAD"], cwd=checkout, timeout_s=timeout_s)
            if head_proc.returncode == 0:
                return True, f"reset failed; reused existing checkout: {(proc.stderr or proc.stdout).strip()}"
        return proc.returncode == 0, (proc.stderr or proc.stdout).strip()
    if checkout.exists():
        shutil.rmtree(checkout)
    proc = run_command(["git", "clone", "--depth", "1", git_url, str(checkout)], timeout_s=timeout_s)
    return proc.returncode == 0, (proc.stderr or proc.stdout).strip()


def ensure_common_remappings(checkout: Path) -> None:
    candidates = [
        ("@openzeppelin/contracts/", "lib/openzeppelin-contracts/contracts/"),
        ("@openzeppelin/contracts-upgradeable/", "lib/openzeppelin-contracts-upgradeable/contracts/"),
        ("openzeppelin/", "lib/openzeppelin-contracts/contracts/"),
        ("openzeppelin-upgradeable/", "lib/openzeppelin-contracts-upgradeable/contracts/"),
        ("@prb/math/", "lib/prb-math/"),
        ("@prb-math/", "lib/prb-math/"),
        ("@chainlink/contracts/", "lib/chainlink/contracts/"),
        ("solmate/", "lib/solmate/src/"),
        ("hardhat/", "node_modules/hardhat/"),
        ("abdk-libraries-solidity/", "node_modules/abdk-libraries-solidity/"),
    ]
    lines: list[str] = []
    remappings_path = checkout / "remappings.txt"
    if remappings_path.exists():
        lines = remappings_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    existing_prefixes = {line.split("=", 1)[0] for line in lines if "=" in line}
    changed = False
    for prefix, target in candidates:
        if prefix in existing_prefixes:
            continue
        if (checkout / target).exists():
            lines.append(f"{prefix}={target}")
            existing_prefixes.add(prefix)
            changed = True
    if changed:
        remappings_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    node_modules = checkout / "node_modules"
    link_candidates = [
        (checkout / "lib/openzeppelin-contracts/contracts", node_modules / "@openzeppelin/contracts"),
        (checkout / "lib/openzeppelin-contracts-upgradeable/contracts", node_modules / "@openzeppelin/contracts-upgradeable"),
        (checkout / "lib/chainlink/contracts", node_modules / "@chainlink/contracts"),
    ]
    for source, link in link_candidates:
        if not source.exists() or link.exists():
            continue
        link.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.symlink(os.path.relpath(source, link.parent), link)
        except OSError:
            pass


def find_project_root(source_file: Path, checkout: Path) -> Path:
    checkout = checkout.resolve()
    current = source_file.resolve().parent
    markers = {"foundry.toml", "remappings.txt"}
    while True:
        if any((current / marker).exists() for marker in markers):
            return current
        if current == checkout or current.parent == current:
            return checkout
        current = current.parent


def normalize_candidate(candidate: str) -> str:
    candidate = unquote(candidate.strip().strip("`'\"<>()[]{}.,;:"))
    if not candidate:
        return ""
    if candidate.startswith("http://") or candidate.startswith("https://"):
        try:
            parsed = urlparse(candidate)
        except ValueError:
            return ""
        parts = parsed.path.strip("/").split("/")
        if "blob" in parts:
            idx = parts.index("blob")
            if len(parts) > idx + 2:
                candidate = "/".join(parts[idx + 2 :])
        elif "tree" in parts:
            return ""
    candidate = candidate.split("#", 1)[0].split("?", 1)[0]
    candidate = candidate.removeprefix("./").lstrip("/")
    candidate = re.sub(r"/+", "/", candidate)
    return candidate if candidate.endswith(".sol") else ""


def markdown_candidates(repo: Path) -> list[str]:
    names = ["README.md", "readme.md", "Readme.md", "SCOPE.md", "scope.md", "Scope.md"]
    files = [repo / name for name in names if (repo / name).is_file()]
    files.extend(sorted(repo.glob("**/scope*.md"))[:20])
    files.extend(sorted(repo.glob("**/*scope*.md"))[:20])
    seen_files: set[Path] = set()
    candidates: list[str] = []
    for path in files:
        if path in seen_files or not path.is_file():
            continue
        seen_files.add(path)
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for match in re.finditer(r"(?:https?://[^\s)>'\"]+|[\w@./ -]+?\.sol)(?:#[A-Za-z0-9-]+)?", text):
            candidate = normalize_candidate(match.group(0))
            if candidate:
                candidates.append(candidate)
    return candidates


def is_excluded(path: Path, include_tests: bool) -> bool:
    parts = set(path.parts)
    if parts & DEFAULT_EXCLUDED_DIRS:
        return True
    if not include_tests and parts & DEFAULT_TEST_DIRS:
        return True
    name = path.name.lower()
    if not include_tests and (name.endswith(".t.sol") or "mock" in name):
        return True
    return False


def resolve_candidates(repo: Path, candidates: Iterable[str]) -> list[Path]:
    resolved: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        direct = repo / candidate
        options = [direct]
        parts = Path(candidate).parts
        for idx, part in enumerate(parts):
            if part in {"src", "contracts", "contract", "protocol"}:
                options.append(repo / Path(*parts[idx:]))
        for option in options:
            try:
                option = option.resolve()
                option.relative_to(repo.resolve())
            except ValueError:
                continue
            if option.is_file() and option.suffix == ".sol" and option not in seen:
                seen.add(option)
                resolved.append(option)
                break
    return resolved


def scan_solidity(repo: Path, include_tests: bool) -> list[Path]:
    files: list[Path] = []
    for path in repo.rglob("*.sol"):
        rel = path.relative_to(repo)
        if is_excluded(rel, include_tests):
            continue
        files.append(path)
    def score(path: Path) -> tuple[int, str]:
        rel = path.relative_to(repo)
        parts = rel.parts
        priority = 3
        if parts and parts[0] in {"src", "contracts", "protocol"}:
            priority = 0
        elif "src" in parts or "contracts" in parts:
            priority = 1
        elif path.name.lower().endswith("interface.sol") or "interface" in {p.lower() for p in parts}:
            priority = 4
        return priority, str(rel)
    return sorted(files, key=score)


def collect_targets(repo: Path, include_tests: bool, per_project_limit: int) -> tuple[list[tuple[Path, str]], str]:
    scoped = resolve_candidates(repo, markdown_candidates(repo))
    if scoped:
        targets = [(path, "readme_scope") for path in scoped if not is_excluded(path.relative_to(repo), include_tests)]
        reason = "readme_scope"
    else:
        targets = [(path, "repo_scan") for path in scan_solidity(repo, include_tests)]
        reason = "repo_scan"
    deduped: list[tuple[Path, str]] = []
    seen: set[Path] = set()
    for path, source_reason in targets:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        deduped.append((path, source_reason))
    if per_project_limit > 0:
        deduped = deduped[:per_project_limit]
    return deduped, reason


def flatten_project(row: dict[str, str], args: argparse.Namespace) -> dict[str, object]:
    project_id = row["project_id"]
    title = row["title"]
    folder = Path(row["output_dir"]).name if row.get("output_dir") else f"{safe_name(title)}_{project_id}"
    target_dir = args.output_dir.resolve() / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    done_marker = target_dir / ".fallback_done"
    if done_marker.exists() and not args.force:
        return {"row": row["row"], "project_id": project_id, "title": title, "status": "skipped", "message": "fallback marker exists"}

    checkout = args.cache_dir.resolve() / f"{safe_name(title, 90)}_{project_id}"
    ok, message = clone_or_update(row["repo"], checkout, args.command_timeout)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_dir = target_dir / "fallback_repo_flatten" / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)
    if not ok:
        summary = {"project_id": project_id, "title": title, "repo": row["repo"], "status": "clone_failed", "error": message}
        (run_dir / "fallback_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"row": row["row"], "project_id": project_id, "title": title, "status": "clone_failed", "message": message[:300]}

    submodule_status = "not_requested"
    submodule_error = ""
    if args.submodules:
        submodule_proc = run_command(
            ["git", "submodule", "update", "--init", "--recursive", "--depth", "1"],
            cwd=checkout,
            timeout_s=args.command_timeout,
        )
        if submodule_proc.returncode == 0:
            submodule_status = "ok"
        else:
            submodule_status = "failed"
            submodule_error = (submodule_proc.stderr or submodule_proc.stdout).strip()[:4000]

    ensure_common_remappings(checkout)

    targets, target_reason = collect_targets(checkout, args.include_tests, args.per_project_limit)
    raw_dir = run_dir / "flatten_raw"
    sorted_dir = run_dir / "flatten_sorted"
    original_dir = run_dir / "original_sources"
    raw_dir.mkdir(parents=True, exist_ok=True)
    sorted_dir.mkdir(parents=True, exist_ok=True)
    original_dir.mkdir(parents=True, exist_ok=True)

    records: list[FallbackRecord] = []
    for source_file, source_reason in targets:
        rel = source_file.relative_to(checkout)
        digest = hashlib.sha1(str(rel).encode()).hexdigest()[:8]
        base = safe_name(f"{rel.with_suffix('').as_posix()}__{digest}", 160)
        raw_out = raw_dir / f"{base}.flatten.sol"
        sorted_out = sorted_dir / f"{base}.sorted.sol"
        original_path = original_dir / rel
        original_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, original_path)

        command_cwd = find_project_root(source_file, checkout)
        ensure_common_remappings(command_cwd)
        flatten_proc = run_command([args.forge_bin, "flatten", str(source_file), "-o", str(raw_out)], cwd=command_cwd, timeout_s=args.command_timeout)
        if flatten_proc.returncode != 0:
            records.append(FallbackRecord(
                project_id, title, row["repo"], rel.as_posix(), str(source_file), str(original_path),
                str(raw_out), str(sorted_out), "forge_failed", (flatten_proc.stderr or flatten_proc.stdout).strip()[:4000], source_reason,
            ))
            continue
        fix_proc = run_command([args.python_bin, str(args.fix_script.resolve()), str(raw_out), str(sorted_out)], cwd=command_cwd, timeout_s=args.command_timeout)
        if fix_proc.returncode != 0:
            records.append(FallbackRecord(
                project_id, title, row["repo"], rel.as_posix(), str(source_file), str(original_path),
                str(raw_out), str(sorted_out), "fix_failed", (fix_proc.stderr or fix_proc.stdout).strip()[:4000], source_reason,
            ))
            continue
        records.append(FallbackRecord(
            project_id, title, row["repo"], rel.as_posix(), str(source_file), str(original_path),
            str(raw_out), str(sorted_out), "ok", source_reason=source_reason,
        ))

    summary = {
        "project_id": project_id,
        "title": title,
        "repo": row["repo"],
        "output_dir": str(run_dir),
        "target_selection": target_reason,
        "target_count": len(targets),
        "flatten_count": len(records),
        "flatten_ok_count": sum(1 for item in records if item.status == "ok"),
        "original_source_count": len(records),
        "submodule_status": submodule_status,
        "submodule_error": submodule_error,
    }
    (run_dir / "fallback_manifest.json").write_text(json.dumps([asdict(item) for item in records], indent=2, ensure_ascii=False), encoding="utf-8")
    (run_dir / "fallback_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    with (run_dir / "fallback_targets.csv").open("w", newline="", encoding="utf-8-sig") as f:
        fields = list(FallbackRecord.__dataclass_fields__.keys())
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in records:
            writer.writerow(asdict(item))

    flatten_ok_count = summary["flatten_ok_count"]
    flatten_count = summary["flatten_count"]
    if flatten_count == 0:
        status = "no_targets"
    elif flatten_ok_count == 0:
        status = "no_flatten_ok"
    elif flatten_ok_count == flatten_count:
        status = "success"
        (target_dir / ".fallback_success").write_text(datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), encoding="utf-8")
    else:
        status = "partial_success"
        (target_dir / ".fallback_partial").write_text(datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), encoding="utf-8")
    done_marker.write_text(datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), encoding="utf-8")
    return {
        "row": row["row"],
        "project_id": project_id,
        "title": title,
        "status": status,
        "message": f"{summary['flatten_ok_count']}/{summary['flatten_count']} flatten ok; targets={summary['target_count']}",
    }


def append_status(path: Path, result: dict[str, object]) -> None:
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8-sig") as f:
        fields = ["row", "project_id", "title", "status", "message"]
        writer = csv.DictWriter(f, fieldnames=fields)
        if not exists:
            writer.writeheader()
        writer.writerow({field: result.get(field, "") for field in fields})


def main() -> int:
    args = parse_args()
    rows = read_rows(args.access_csv, args.start_at, args.limit)
    if not rows:
        print("No accessible fallback rows to process.")
        return 0
    if not args.fix_script.exists():
        raise SystemExit(f"fix script not found: {args.fix_script}")
    if shutil.which(args.forge_bin) is None:
        raise SystemExit(f"forge not found: {args.forge_bin}")

    status_path = args.output_dir.resolve() / "_batch_logs" / "repo_fallback_status.csv"
    print("== Code4rena repo fallback flatten ==")
    print(f"rows             : {len(rows)}")
    print(f"output_dir       : {args.output_dir.resolve()}")
    print(f"cache_dir        : {args.cache_dir.resolve()}")
    print(f"jobs             : {args.jobs}")
    print(f"per_project_limit: {args.per_project_limit or '<none>'}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as executor:
        future_map = {executor.submit(flatten_project, row, args): row for row in rows}
        for future in concurrent.futures.as_completed(future_map):
            row = future_map[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {
                    "row": row.get("row", ""),
                    "project_id": row.get("project_id", ""),
                    "title": row.get("title", ""),
                    "status": "script_exception",
                    "message": repr(exc)[:500],
                }
            append_status(status_path, result)
            print(f"[{result['row']}] {result['status']} {result['title']} - {result['message']}")
    print(f"status: {status_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
