#!/usr/bin/env python3
r"""
Code4rena -> Solidity flatten pipeline.

Given a Code4rena audit project id, this script can:
1. Fetch submission/finding details from Code4rena API, or load them from a local JSON file.
2. Extract useful fields such as severity, judge status, PoC, body, and linesOfCode URLs.
3. Download the GitHub repository/ref from linesOfCode URLs and map paths to that checkout.
4. Run `forge flatten` for the referenced Solidity files.
5. Run fix_flatten_order.py on the raw flatten output.

Typical usage:
    python code4rena_flatten_pipeline.py \
        --project c9MhophgwGP \
        --repo D:\work\...\2025-06-panoptic \
        --cookie-env CODE4RENA_COOKIE

If you already have a Code4rena submission JSON dump:
    python code4rena_flatten_pipeline.py \
        --project c9MhophgwGP \
        --repo D:\work\...\2025-06-panoptic \
        --submissions-json submission.json
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urlparse

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

CODE4RENA_API = "https://code4rena.com/api/v1"
GITHUB_BLOB_RE = re.compile(r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/blob/(?P<ref>[^/]+)/(?P<path>[^#]+)(?:#(?P<anchor>.+))?")
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "c4_pipeline_output"
DEFAULT_FIX_SCRIPT = ROOT / "c4_pipeline_output" / "_tools" / "identity_fix_flatten_order.py"
PROXY_VARS = [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy", "ftp_proxy", "FTP_PROXY",
]


@dataclass
class FindingRecord:
    project_id: str
    submission_index: str = ""
    api_submission_id: str = ""
    uid: str = ""
    number: str = ""
    title: str = ""
    severity: str = ""
    validity: str = ""
    quality: str = ""
    handle: str = ""
    lines_of_code: list[str] = field(default_factory=list)
    body: str = ""
    proof_of_concept: str = ""
    detail_url: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GitHubBlobRef:
    owner: str
    repo: str
    ref: str
    path: str
    line: str = ""


@dataclass
class FlattenRecord:
    project_id: str
    finding_key: str
    title: str
    severity: str
    validity: str
    code_url: str
    relative_path: str
    target_line: str
    raw_flatten_path: str
    sorted_flatten_path: str
    status: str
    error: str = ""
    github_owner: str = ""
    github_repo: str = ""
    github_ref: str = ""
    source_root: str = ""
    source_path: str = ""
    original_source_path: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect Code4rena findings and flatten referenced Solidity files."
    )
    parser.add_argument("--project", required=True, help="Code4rena audit UID, e.g. c9MhophgwGP.")
    parser.add_argument("--repo", type=Path, help="Local checkout of the audited repository.")
    parser.add_argument(
        "--submissions-json",
        type=Path,
        help="Use a local Code4rena submissions JSON dump instead of fetching from API.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for JSON/CSV/Markdown and flattened Solidity outputs.",
    )
    parser.add_argument(
        "--fix-script",
        type=Path,
        default=DEFAULT_FIX_SCRIPT,
        help="Path to fix_flatten_order.py.",
    )
    parser.add_argument("--forge-bin", default="forge", help="forge executable name/path.")
    parser.add_argument("--python-bin", default=sys.executable, help="Python executable used for fix_flatten_order.py.")
    parser.add_argument(
        "--github-cache-dir",
        type=Path,
        help="Directory used to cache GitHub checkouts for linesOfCode refs.",
    )
    parser.add_argument(
        "--github-submodules",
        choices=["none", "first-level", "recursive"],
        default="none",
        help="Submodule update mode for auto-downloaded GitHub checkouts.",
    )
    parser.add_argument(
        "--command-timeout",
        type=int,
        default=300,
        help="Timeout in seconds for each git/forge/fix subprocess.",
    )
    parser.add_argument(
        "--no-download-github",
        action="store_true",
        help="Do not auto-download GitHub refs; only use --repo as the source root.",
    )
    parser.add_argument("--cookie", help="Code4rena browser Cookie value. Prefer --cookie-env.")
    parser.add_argument("--cookie-env", default="CODE4RENA_COOKIE", help="Environment variable containing Code4rena Cookie.")
    parser.add_argument("--proxy", help="Optional HTTP/HTTPS proxy, e.g. http://127.0.0.1:7890.")
    parser.add_argument("--api-workers", type=int, default=1, help="Parallel workers for fetching submission details.")
    parser.add_argument("--max-submissions", type=int, help="Limit fetched submission count for quick tests.")
    parser.add_argument("--include-invalid", action="store_true", help="Also process findings judged invalid.")
    parser.add_argument(
        "--severity",
        action="append",
        help="Only process this severity. Can be repeated, e.g. --severity high --severity medium.",
    )
    parser.add_argument("--skip-flatten", action="store_true", help="Only collect/export finding data.")
    parser.add_argument("--dry-run", action="store_true", help="Show planned flatten targets without running forge.")
    parser.add_argument("--sleep", type=float, default=0.4, help="Delay between API detail requests.")
    return parser.parse_args()


def make_session(cookie: str | None, proxy: str | None):
    if requests is None:
        raise RuntimeError("The requests package is required for API fetching. Install it or use --submissions-json.")
    session = requests.Session()
    session.trust_env = False
    headers = {
        "User-Agent": "Mozilla/5.0 Code4renaFlattenPipeline/1.0",
        "Accept": "application/json",
    }
    if cookie:
        # Code4rena has used both LOGIN and C4AUTH-LOGIN in local scripts/browser
        # sessions. If the caller provides LOGIN=token, send both names.
        if cookie.startswith("LOGIN=") and "C4AUTH-LOGIN=" not in cookie:
            token = cookie.split("=", 1)[1]
            cookie = f"LOGIN={token}; C4AUTH-LOGIN={token}"
        headers["Cookie"] = cookie
    session.headers.update(headers)
    if proxy:
        session.proxies.update({"http": proxy, "https": proxy})
    return session


def get_with_retries(session, url: str, *, params: dict[str, Any] | None = None, timeout: int = 30, attempts: int = 5):
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            response = session.get(url, params=params, timeout=timeout)
            if response.status_code in {429, 500, 502, 503, 504} and attempt < attempts:
                time.sleep(min(2 ** (attempt - 1), 8))
                continue
            return response
        except Exception as exc:
            last_exc = exc
            if attempt >= attempts:
                raise
            time.sleep(min(2 ** (attempt - 1), 8))
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("unreachable retry state")


def fetch_submission_page(session, project_id: str, page: int = 1, per_page: int = 25) -> dict[str, Any]:
    url = f"{CODE4RENA_API}/audits/{project_id}/submissions"
    response = get_with_retries(session, url, params={"page": page, "perPage": per_page}, timeout=20)
    if response.status_code == 401:
        raise RuntimeError(
            "Code4rena submissions API returned 401 Unauthorized. "
            "Export CODE4RENA_COOKIE or set CODE4RENA_COOKIE in the bash script."
        )
    response.raise_for_status()
    return response.json()


def fetch_submission_numbers(session, project_id: str, limit: int | None) -> list[int]:
    first_page = fetch_submission_page(session, project_id, page=1)
    pagination = first_page.get("pagination", {}) or {}
    last_page = int(pagination.get("lastPage") or 1)
    total = int(pagination.get("total") or 0)

    numbers: list[int] = []

    def collect(data: dict[str, Any]) -> None:
        for item in data.get("data", {}).get("submissions", []) or []:
            number = item.get("number")
            if number is None:
                continue
            try:
                numbers.append(int(number))
            except (TypeError, ValueError):
                continue

    collect(first_page)
    page = 2
    while page <= last_page and (limit is None or len(numbers) < limit):
        collect(fetch_submission_page(session, project_id, page=page))
        page += 1

    if limit is not None:
        numbers = numbers[:limit]
    print(f"Found {total or len(numbers)} submissions for project {project_id}; fetching {len(numbers)} details.")
    return numbers


def fetch_submission_detail(session, project_id: str, index: int) -> dict[str, Any]:
    url = f"{CODE4RENA_API}/audits/{project_id}/submissions/{index}"
    response = get_with_retries(session, url, timeout=30)
    if response.status_code == 401:
        return {"_error": "401 Unauthorized. Set CODE4RENA_COOKIE.", "_index": index}
    if response.status_code == 404:
        return {"_error": "404 Not Found", "_index": index}
    response.raise_for_status()
    data = response.json()
    if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
        data = data["data"]
    data["_index"] = index
    return data


def fetch_submissions(project_id: str, cookie: str | None, proxy: str | None, limit: int | None, sleep_s: float) -> list[dict[str, Any]]:
    session = make_session(cookie, proxy)
    submission_numbers = fetch_submission_numbers(session, project_id, limit)

    rows: list[dict[str, Any]] = []
    total_to_fetch = len(submission_numbers)
    for offset, index in enumerate(submission_numbers, 1):
        try:
            detail = fetch_submission_detail(session, project_id, index)
        except Exception as exc:
            detail = {"_error": str(exc), "_index": index}
        rows.append(detail)
        label = detail.get("title") or detail.get("_error") or "ok"
        print(f"  [{offset}/{total_to_fetch}] #{index}: {label}")
        if sleep_s > 0:
            time.sleep(sleep_s)
    return rows


def fetch_submissions_parallel(
    project_id: str,
    cookie: str | None,
    proxy: str | None,
    limit: int | None,
    sleep_s: float,
    api_workers: int,
) -> list[dict[str, Any]]:
    session = make_session(cookie, proxy)
    submission_numbers = fetch_submission_numbers(session, project_id, limit)
    total_to_fetch = len(submission_numbers)
    if total_to_fetch == 0:
        return []

    if api_workers <= 1:
        return fetch_submissions(project_id, cookie, proxy, limit, sleep_s)

    workers = max(1, min(api_workers, total_to_fetch))
    rows: list[dict[str, Any] | None] = [None] * total_to_fetch

    def worker(position: int, submission_index: int) -> tuple[int, int, dict[str, Any]]:
        worker_session = make_session(cookie, proxy)
        try:
            detail = fetch_submission_detail(worker_session, project_id, submission_index)
        except Exception as exc:
            detail = {"_error": str(exc), "_index": submission_index}
        return position, submission_index, detail

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = []
        for position, submission_index in enumerate(submission_numbers):
            futures.append(executor.submit(worker, position, submission_index))
            if sleep_s > 0:
                time.sleep(sleep_s)

        completed = 0
        for future in as_completed(futures):
            position, submission_index, detail = future.result()
            rows[position] = detail
            completed += 1
            label = detail.get("title") or detail.get("_error") or "ok"
            print(f"  [{completed}/{total_to_fetch}] #{submission_index}: {label}")

    return [row for row in rows if row is not None]


def load_submissions_json(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        raise ValueError(f"Unsupported JSON root in {path}")

    for keys in [
        ("data", "submissions"),
        ("submissions",),
        ("data",),
    ]:
        node: Any = data
        ok = True
        for key in keys:
            if isinstance(node, dict) and key in node:
                node = node[key]
            else:
                ok = False
                break
        if ok and isinstance(node, list):
            return node
    if "title" in data or "linesOfCode" in data:
        return [data]
    raise ValueError(f"Could not find a submissions list in {path}")


def split_code_urls(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        pieces = value
    else:
        pieces = re.split(r"[\s,]+", str(value))
    return [p.strip() for p in pieces if p and "github.com" in p and "/blob/" in p]


def normalize_submission(project_id: str, item: dict[str, Any]) -> FindingRecord:
    latest_eval = item.get("latestEvaluations") or {}
    user = item.get("user") or {}
    finding = item.get("finding") or {}
    index = item.get("_index") or item.get("submission_index") or item.get("number") or ""
    handle = item.get("handle") or user.get("handle") or ""

    lines_of_code = split_code_urls(item.get("linesOfCode") or item.get("lines_of_code") or item.get("loc"))
    if not lines_of_code:
        # Older contests only embed the "# Lines of code" URLs in the report body.
        lines_of_code = split_code_urls(item.get("body") or "")

    return FindingRecord(
        project_id=project_id,
        submission_index=str(index),
        api_submission_id=str(item.get("id") or item.get("api_submission_id") or ""),
        uid=str(item.get("uid") or ""),
        number=str(item.get("number") or finding.get("number") or ""),
        title=str(item.get("title") or ""),
        severity=str(item.get("severity") or latest_eval.get("severity") or ""),
        validity=str(latest_eval.get("validity") or item.get("validity") or ""),
        quality=str(latest_eval.get("quality") or item.get("quality") or ""),
        handle=str(handle),
        lines_of_code=lines_of_code,
        body=str(item.get("body") or ""),
        proof_of_concept=str(item.get("proofOfConcept") or item.get("proof_of_concept") or ""),
        detail_url=f"{CODE4RENA_API}/audits/{project_id}/submissions/{index}" if index else "",
        raw=item,
    )


def filter_findings(records: Iterable[FindingRecord], include_invalid: bool, severities: list[str] | None) -> list[FindingRecord]:
    severity_set = {s.lower() for s in severities} if severities else None
    filtered: list[FindingRecord] = []
    for record in records:
        if severity_set and record.severity.lower() not in severity_set:
            continue
        if not include_invalid and record.validity.lower() == "invalid":
            continue
        if not record.lines_of_code:
            continue
        filtered.append(record)
    return filtered


def parse_github_blob_url(url: str) -> GitHubBlobRef:
    match = GITHUB_BLOB_RE.match(url.strip())
    if not match:
        raise ValueError(f"Unsupported GitHub blob URL: {url}")
    rel_path = unquote(match.group("path")).replace("\\", "/")
    anchor = match.group("anchor") or ""
    line = ""
    line_match = re.search(r"L(\d+)", anchor)
    if line_match:
        line = line_match.group(1)
    return GitHubBlobRef(
        owner=match.group("owner"),
        repo=match.group("repo"),
        ref=match.group("ref"),
        path=rel_path,
        line=line,
    )


def safe_name(value: str, max_len: int = 120) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")
    return value[:max_len] or "item"


def short_ref_name(ref: str) -> str:
    if re.fullmatch(r"[0-9a-fA-F]{40}", ref):
        return ref[:8]
    return safe_name(ref, 24)


def flatten_output_base(finding_key: str, blob: GitHubBlobRef, used_names: set[str]) -> str:
    contract_name = safe_name(Path(blob.path).stem, 48)
    ref_name = short_ref_name(blob.ref)
    base = safe_name(f"{finding_key}__{contract_name}__{ref_name}", 100)
    if base not in used_names:
        used_names.add(base)
        return base

    digest = hashlib.sha1(f"{blob.owner}/{blob.repo}/{blob.ref}/{blob.path}".encode()).hexdigest()[:8]
    candidate = safe_name(f"{base}__{digest}", 120)
    suffix = 2
    while candidate in used_names:
        candidate = safe_name(f"{base}__{digest}_{suffix}", 120)
        suffix += 1
    used_names.add(candidate)
    return candidate


def run_command(cmd: list[str], cwd: Path | None = None, timeout_s: int = 300) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    for key in PROXY_VARS:
        env.pop(key, None)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env.setdefault("GIT_ASKPASS", "true")
    try:
        return subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(
            cmd,
            124,
            stdout=exc.stdout or "",
            stderr=f"Timed out after {timeout_s}s",
        )


def github_checkout_dir(cache_dir: Path, blob: GitHubBlobRef) -> Path:
    name = "__".join([
        safe_name(blob.owner),
        safe_name(blob.repo),
        safe_name(blob.ref, 80),
    ])
    return cache_dir / name


def ensure_github_checkout(
    blob: GitHubBlobRef,
    cache_dir: Path,
    submodule_mode: str,
    command_timeout: int,
) -> tuple[Path | None, str]:
    checkout = github_checkout_dir(cache_dir, blob)
    repo_url = f"https://github.com/{blob.owner}/{blob.repo}.git"
    cache_dir.mkdir(parents=True, exist_ok=True)

    if not (checkout / ".git").exists():
        if checkout.exists() and any(checkout.iterdir()):
            return None, f"GitHub cache path exists but is not a git checkout: {checkout}"
        clone_proc = run_command(["git", "clone", "--filter=blob:none", "--no-checkout", repo_url, str(checkout)], timeout_s=command_timeout)
        if clone_proc.returncode != 0:
            return None, (clone_proc.stderr or clone_proc.stdout).strip()

    checkout_proc = run_command(["git", "checkout", "--force", blob.ref], cwd=checkout, timeout_s=command_timeout)
    if checkout_proc.returncode != 0:
        fetch_proc = run_command(["git", "fetch", "--all", "--tags"], cwd=checkout, timeout_s=command_timeout)
        if fetch_proc.returncode != 0:
            return None, (fetch_proc.stderr or fetch_proc.stdout).strip()
        checkout_proc = run_command(["git", "checkout", "--force", blob.ref], cwd=checkout, timeout_s=command_timeout)
        if checkout_proc.returncode != 0:
            return None, (checkout_proc.stderr or checkout_proc.stdout).strip()

    if submodule_mode != "none":
        submodule_cmd = ["git", "submodule", "update", "--init", "--depth", "1"]
        if submodule_mode == "recursive":
            submodule_cmd.append("--recursive")
        submodule_proc = run_command(submodule_cmd, cwd=checkout, timeout_s=command_timeout)
        if submodule_proc.returncode != 0:
            # Some submodules pin a commit that is not reachable by a depth-1
            # clone of their default branch/tag; retry with a full clone.
            fallback_cmd = ["git", "submodule", "update", "--init"]
            if submodule_mode == "recursive":
                fallback_cmd.append("--recursive")
            fallback_proc = run_command(fallback_cmd, cwd=checkout, timeout_s=command_timeout)
            if fallback_proc.returncode != 0:
                return None, (fallback_proc.stderr or fallback_proc.stdout).strip()

    return checkout, ""


def resolve_source_root(
    blob: GitHubBlobRef,
    fallback_repo: Path | None,
    github_cache_dir: Path,
    download_github: bool,
    github_submodules: str,
    command_timeout: int,
) -> tuple[Path | None, Path, str]:
    if download_github:
        checkout, error = ensure_github_checkout(blob, github_cache_dir, github_submodules, command_timeout)
        if checkout is None:
            return None, Path(blob.path), error
        return checkout, checkout / blob.path, ""

    if fallback_repo is None:
        return None, Path(blob.path), "--repo is required when GitHub auto-download is disabled."
    return fallback_repo, fallback_repo / blob.path, ""


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_findings_csv(path: Path, records: list[FindingRecord]) -> None:
    fieldnames = [
        "project_id", "submission_index", "api_submission_id", "uid", "number",
        "title", "severity", "validity", "quality", "handle", "lines_of_code", "detail_url",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            row = asdict(record)
            row["lines_of_code"] = "\n".join(record.lines_of_code)
            row.pop("body", None)
            row.pop("proof_of_concept", None)
            row.pop("raw", None)
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def write_markdown_reports(report_dir: Path, records: list[FindingRecord]) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    for record in records:
        key = safe_name(record.submission_index or record.uid or record.number or record.title)
        md = [
            f"# {record.title or 'Untitled finding'}",
            "",
            f"- Project: {record.project_id}",
            f"- Submission: {record.submission_index}",
            f"- Author: {record.handle}",
            f"- Severity: {record.severity}",
            f"- Validity: {record.validity}",
            f"- Quality: {record.quality}",
            "- Code links:",
        ]
        md.extend([f"  - {url}" for url in record.lines_of_code])
        md.extend(["", "## Vulnerability Details", "", record.body or "", ""])
        if record.proof_of_concept.strip():
            md.extend(["## Proof of Concept", "", "```", record.proof_of_concept, "```", ""])
        (report_dir / f"{key}.md").write_text("\n".join(md), encoding="utf-8")


def find_forge_root(source_file: Path, source_root: Path) -> Path:
    """Return the nearest ancestor of ``source_file`` that contains a Foundry
    project marker (foundry.toml, remappings.txt, then package.json). Falls back
    to the git checkout root so repos without a nested project keep working."""
    source_root = source_root.resolve()
    current = source_file.resolve().parent
    candidates: list[Path] = []
    while True:
        candidates.append(current)
        if current == source_root:
            break
        if current.parent == current:
            break
        current = current.parent
    for marker in ("foundry.toml", "remappings.txt", "package.json"):
        for cand in candidates:
            if (cand / marker).exists():
                return cand
    return source_root


def install_npm_deps(project_root: Path, command_timeout: int) -> str:
    """Install npm dependencies for Hardhat projects (proxy already stripped by
    run_command). Missing package.json or an existing node_modules directory is
    treated as already satisfied; any install failure is returned as an error
    string so flatten can still be attempted."""
    if not (project_root / "package.json").exists():
        return ""
    if (project_root / "node_modules").exists():
        return ""
    npm_bin = shutil.which("npm") or "npm"
    install_cmd = [npm_bin, "install", "--no-audit", "--no-fund", "--loglevel=error"]
    proc = run_command(
        install_cmd,
        cwd=project_root,
        timeout_s=command_timeout,
    )
    if proc.returncode != 0:
        return (proc.stderr or proc.stdout).strip()
    if not (project_root / "node_modules").exists():
        return "npm install exited 0 but node_modules was not created"
    return ""


def flatten_targets(
    project_id: str,
    repo: Path | None,
    output_dir: Path,
    fix_script: Path,
    forge_bin: str,
    python_bin: str,
    records: list[FindingRecord],
    dry_run: bool,
    github_cache_dir: Path,
    download_github: bool,
    github_submodules: str,
    command_timeout: int,
) -> list[FlattenRecord]:
    raw_dir = output_dir / "flatten_raw"
    sorted_dir = output_dir / "flatten_sorted"
    original_sources_dir = output_dir / "original_sources"
    raw_dir.mkdir(parents=True, exist_ok=True)
    sorted_dir.mkdir(parents=True, exist_ok=True)
    original_sources_dir.mkdir(parents=True, exist_ok=True)

    seen: set[tuple[str, str, str, str, str]] = set()
    flatten_cache: dict[tuple[str, str, str, str], FlattenRecord] = {}
    source_root_cache: dict[tuple[str, str, str], tuple[Path | None, str]] = {}
    npm_install_cache: set[Path] = set()
    used_output_names: set[str] = set()
    results: list[FlattenRecord] = []

    for record in records:
        finding_key = safe_name(record.submission_index or record.uid or record.number or record.title)
        for code_url in record.lines_of_code:
            try:
                blob = parse_github_blob_url(code_url)
            except Exception as exc:
                results.append(FlattenRecord(project_id, finding_key, record.title, record.severity, record.validity, code_url, "", "", "", "", "parse_error", str(exc)))
                continue

            if (finding_key, blob.owner, blob.repo, blob.ref, blob.path) in seen:
                continue
            seen.add((finding_key, blob.owner, blob.repo, blob.ref, blob.path))

            cache_key = (blob.owner, blob.repo, blob.ref, blob.path)
            cached = flatten_cache.get(cache_key)
            if cached is not None:
                results.append(FlattenRecord(
                    project_id,
                    finding_key,
                    record.title,
                    record.severity,
                    record.validity,
                    code_url,
                    blob.path,
                    blob.line,
                    cached.raw_flatten_path,
                    cached.sorted_flatten_path,
                    cached.status,
                    cached.error,
                    github_owner=cached.github_owner,
                    github_repo=cached.github_repo,
                    github_ref=cached.github_ref,
                    source_root=cached.source_root,
                    source_path=cached.source_path,
                    original_source_path=cached.original_source_path,
                ))
                continue

            source_cache_key = (blob.owner, blob.repo, blob.ref)
            if download_github:
                if source_cache_key not in source_root_cache:
                    source_root_cache[source_cache_key] = ensure_github_checkout(
                        blob,
                        github_cache_dir,
                        github_submodules,
                        command_timeout,
                    )
                source_root, resolve_error = source_root_cache[source_cache_key]
                source_file = (source_root / blob.path) if source_root is not None else Path(blob.path)
            else:
                source_root = repo
                source_file = (repo / blob.path) if repo is not None else Path(blob.path)
                resolve_error = "" if repo is not None else "--repo is required when GitHub auto-download is disabled."

            out_base = flatten_output_base(finding_key, blob, used_output_names)
            raw_out = raw_dir / f"{out_base}.flatten.sol"
            sorted_out = sorted_dir / f"{out_base}.sorted.sol"

            record_kwargs = {
                "github_owner": blob.owner,
                "github_repo": blob.repo,
                "github_ref": blob.ref,
                "source_root": str(source_root or ""),
                "source_path": str(source_file),
                "original_source_path": "",
            }

            if resolve_error:
                result = FlattenRecord(project_id, finding_key, record.title, record.severity, record.validity, code_url, blob.path, blob.line, str(raw_out), str(sorted_out), "source_resolve_failed", resolve_error, **record_kwargs)
                flatten_cache[cache_key] = result
                results.append(result)
                continue

            if not source_file.exists():
                result = FlattenRecord(project_id, finding_key, record.title, record.severity, record.validity, code_url, blob.path, blob.line, str(raw_out), str(sorted_out), "missing_source", f"Not found: {source_file}", **record_kwargs)
                flatten_cache[cache_key] = result
                results.append(result)
                continue

            original_source_path = original_sources_dir / safe_name(blob.owner) / safe_name(blob.repo) / safe_name(blob.ref, 80) / blob.path
            original_source_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, original_source_path)
            record_kwargs["original_source_path"] = str(original_source_path)

            forge_root = find_forge_root(source_file, source_root)
            has_package_json = (forge_root / "package.json").exists()
            is_hardhat = has_package_json and not (forge_root / "foundry.toml").exists()

            if dry_run:
                hardhat_flag = " --hardhat" if is_hardhat else ""
                print(f"DRY RUN: {forge_bin} flatten{hardhat_flag} {source_file} -o {raw_out}")
                result = FlattenRecord(project_id, finding_key, record.title, record.severity, record.validity, code_url, blob.path, blob.line, str(raw_out), str(sorted_out), "planned", **record_kwargs)
                flatten_cache[cache_key] = result
                results.append(result)
                continue

            npm_install_error = ""
            if has_package_json and forge_root not in npm_install_cache:
                npm_install_error = install_npm_deps(forge_root, command_timeout)
                npm_install_cache.add(forge_root)

            flatten_cmd = [forge_bin, "flatten"]
            if is_hardhat:
                flatten_cmd.append("--hardhat")
            flatten_cmd.extend([str(source_file), "-o", str(raw_out)])
            flatten_proc = run_command(flatten_cmd, cwd=forge_root, timeout_s=command_timeout)
            if flatten_proc.returncode != 0:
                err = (flatten_proc.stderr or flatten_proc.stdout).strip()
                if npm_install_error:
                    err = f"npm install: {npm_install_error}\n{err}"
                result = FlattenRecord(project_id, finding_key, record.title, record.severity, record.validity, code_url, blob.path, blob.line, str(raw_out), str(sorted_out), "forge_failed", err, **record_kwargs)
                flatten_cache[cache_key] = result
                results.append(result)
                continue

            fix_cmd = [python_bin, str(fix_script), str(raw_out), str(sorted_out)]
            fix_proc = run_command(fix_cmd, cwd=forge_root, timeout_s=command_timeout)
            if fix_proc.returncode != 0:
                err = (fix_proc.stderr or fix_proc.stdout).strip()
                result = FlattenRecord(project_id, finding_key, record.title, record.severity, record.validity, code_url, blob.path, blob.line, str(raw_out), str(sorted_out), "fix_failed", err, **record_kwargs)
                flatten_cache[cache_key] = result
                results.append(result)
                continue

            result = FlattenRecord(project_id, finding_key, record.title, record.severity, record.validity, code_url, blob.path, blob.line, str(raw_out), str(sorted_out), "ok", **record_kwargs)
            flatten_cache[cache_key] = result
            results.append(result)
            print(f"OK: {blob.owner}/{blob.repo}@{blob.ref}:{blob.path} -> {sorted_out}")

    return results


def main() -> int:
    args = parse_args()
    project_id = args.project.strip().rstrip("/")
    if project_id.startswith("http"):
        project_id = urlparse(project_id).path.strip("/").split("/")[-1]

    run_dir = args.output_dir.resolve() / project_id / datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)

    if args.submissions_json:
        raw_submissions = load_submissions_json(args.submissions_json)
    else:
        cookie = args.cookie or os.environ.get(args.cookie_env)
        try:
            if args.api_workers > 1:
                raw_submissions = fetch_submissions_parallel(
                    project_id,
                    cookie,
                    args.proxy,
                    args.max_submissions,
                    args.sleep,
                    args.api_workers,
                )
            else:
                raw_submissions = fetch_submissions(project_id, cookie, args.proxy, args.max_submissions, args.sleep)
        except RuntimeError as exc:
            raise SystemExit(f"ERROR: {exc}") from None

    write_json(run_dir / "raw_submissions.json", raw_submissions)

    all_records = [normalize_submission(project_id, item) for item in raw_submissions if not item.get("_error")]
    selected_records = filter_findings(all_records, args.include_invalid, args.severity)

    write_json(run_dir / "findings.json", [asdict(r) for r in selected_records])
    write_findings_csv(run_dir / "findings.csv", selected_records)
    write_markdown_reports(run_dir / "reports", selected_records)

    print(f"Selected {len(selected_records)} findings with Code4rena code links.")

    flatten_results: list[FlattenRecord] = []
    if not args.skip_flatten:
        repo = args.repo.resolve() if args.repo else None
        if args.no_download_github and repo is None:
            raise SystemExit("--repo is required when --no-download-github is used.")
        if repo is not None and not repo.exists():
            raise SystemExit(f"Repository path does not exist: {repo}")
        if not args.dry_run and not args.fix_script.exists():
            raise SystemExit(f"fix_flatten_order.py not found: {args.fix_script}")
        github_cache_dir = (args.github_cache_dir or (args.output_dir.resolve() / "_github_repos")).resolve()
        flatten_results = flatten_targets(
            project_id=project_id,
            repo=repo,
            output_dir=run_dir,
            fix_script=args.fix_script.resolve(),
            forge_bin=args.forge_bin,
            python_bin=args.python_bin,
            records=selected_records,
            dry_run=args.dry_run,
            github_cache_dir=github_cache_dir,
            download_github=not args.no_download_github,
            github_submodules=args.github_submodules,
            command_timeout=args.command_timeout,
        )
        write_json(run_dir / "flatten_manifest.json", [asdict(r) for r in flatten_results])

    summary = {
        "project_id": project_id,
        "output_dir": str(run_dir),
        "raw_submission_count": len(raw_submissions),
        "selected_finding_count": len(selected_records),
        "flatten_count": len(flatten_results),
        "flatten_ok_count": sum(1 for r in flatten_results if r.status == "ok"),
    }
    write_json(run_dir / "summary.json", summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
