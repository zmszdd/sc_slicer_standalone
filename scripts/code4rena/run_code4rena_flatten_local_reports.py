#!/usr/bin/env python3
r"""
Flatten Code4rena projects from locally cached report dumps.

When the Code4rena submissions API is unavailable (expired cookie / 401), the
pipeline can still build a flatten corpus from previously saved JSON dumps.

Two offline sources are supported:

* ``reports``   -- per-submission files under
                   ``code4rena_reports/<Title>_<uid>/submission_*.json``.
* ``raw_dumps`` -- the largest non-empty ``raw_submissions.json`` previously
                   saved under ``c4_pipeline_output/<Project>/<run>/``.

For each project the script runs ``code4rena_flatten_pipeline.py`` with
``--submissions-json`` so no API auth is needed, and uses a per-project GitHub
cache under ``_github_repos_by_project/<uid>``.

Proxy environment variables are cleared and git terminal prompts are disabled
so stale proxies / private repositories fail fast instead of hanging.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORTS_DIR = ROOT / "code4rena_reports"
DEFAULT_OUTPUT_DIR = ROOT / "c4_pipeline_output"
PIPELINE = ROOT / "scripts" / "code4rena" / "code4rena_flatten_pipeline.py"
DEFAULT_FIX_SCRIPT = DEFAULT_OUTPUT_DIR / "_tools" / "identity_fix_flatten_order.py"

PROXY_VARS = [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy", "ftp_proxy", "FTP_PROXY",
]


class Job:
    def __init__(self, uid: str, title: str, submissions_path: Path, source: str):
        self.uid = uid
        self.title = title
        self.submissions_path = submissions_path
        self.source = source


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--fix-script", type=Path, default=DEFAULT_FIX_SCRIPT)
    parser.add_argument("--python-bin", default=sys.executable)
    parser.add_argument("--forge-bin", default="forge")
    parser.add_argument(
        "--submissions-source",
        choices=["reports", "raw_dumps"],
        default="raw_dumps",
        help="Offline submission source. raw_dumps prefers the largest saved raw_submissions.json.",
    )
    parser.add_argument("--github-submodules", choices=["none", "first-level", "recursive"], default="first-level")
    parser.add_argument("--command-timeout", type=int, default=600)
    parser.add_argument("--jobs", type=int, default=2, help="Parallel projects.")
    parser.add_argument("--start-at", type=int, default=1)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-flatten", action="store_true")
    parser.add_argument("--include-invalid", action="store_true")
    parser.add_argument("--severity", action="append")
    parser.add_argument("--project-ids", nargs="*", help="Only process these Code4rena project ids.")
    return parser.parse_args()


def uid_from_dir_name(name: str) -> str:
    return name.rsplit("_", 1)[-1]


def collect_report_jobs(reports_dir: Path, output_dir: Path, project_ids: list[str] | None) -> list[Job]:
    jobs: list[Job] = []
    for dir_path in sorted(reports_dir.iterdir()):
        if not dir_path.is_dir():
            continue
        submission_files = sorted(dir_path.glob("submission_*.json"))
        if not submission_files:
            continue
        uid = uid_from_dir_name(dir_path.name)
        if project_ids and uid not in project_ids:
            continue
        submissions: list[dict[str, Any]] = []
        for path in submission_files:
            try:
                data = json.loads(path.read_text(encoding="utf-8-sig"))
            except Exception:
                continue
            if isinstance(data, dict):
                submissions.append(data)
        merged = output_dir / "_local_reports" / f"{uid}_submissions.json"
        merged.parent.mkdir(parents=True, exist_ok=True)
        merged.write_text(json.dumps(submissions, ensure_ascii=False), encoding="utf-8")
        jobs.append(Job(uid, dir_path.name, merged, "reports"))
    return jobs


def collect_raw_dump_jobs(output_dir: Path, project_ids: list[str] | None) -> list[Job]:
    best: dict[str, tuple[Path, str, int]] = {}
    for path in sorted(output_dir.glob("*/*/raw_submissions.json")):
        project_dir = path.parent.parent
        if project_dir == output_dir / "_github_repos_by_project":
            continue
        uid = uid_from_dir_name(project_dir.name)
        if project_dir.name == uid:
            # Bare `<uid>/` directories are transient pipeline output, not a
            # stable offline source; only `<Title>_<uid>/` dirs are kept.
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        if not isinstance(data, list) or not data:
            continue
        if project_ids and uid not in project_ids:
            continue
        prev = best.get(uid)
        if prev is None or len(data) > prev[2]:
            best[uid] = (path, project_dir.name, len(data))
    jobs: list[Job] = []
    for uid in sorted(best):
        path, title, count = best[uid]
        jobs.append(Job(uid, title, path, "raw_dumps"))
    return jobs


def clean_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in PROXY_VARS:
        env.pop(key, None)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env.setdefault("GIT_ASKPASS", "true")
    return env


def collect_uid_output(output_dir: Path, uid: str, target_dir: Path) -> None:
    source_dir = output_dir / uid
    if not source_dir.is_dir():
        return
    if source_dir == target_dir:
        return
    target_dir.mkdir(parents=True, exist_ok=True)
    src_prefix = str(source_dir.resolve()) + os.sep
    dst_prefix = str(target_dir.resolve()) + os.sep
    for item in list(source_dir.iterdir()):
        dest = target_dir / item.name
        if dest.exists():
            if dest.is_dir():
                shutil.rmtree(dest, ignore_errors=True)
            else:
                dest.unlink(missing_ok=True)
        item.rename(dest)
    _rewrite_moved_paths(target_dir, src_prefix, dst_prefix)
    source_dir.rmdir()


def _rewrite_moved_paths(target_dir: Path, src_prefix: str, dst_prefix: str) -> None:
    """Rewrite absolute run-dir paths left behind by the pipeline.

    ``code4rena_flatten_pipeline.py`` writes its run under
    ``<output>/<uid>/<timestamp>/`` and stores those absolute paths inside
    ``summary.json`` and ``flatten_manifest.json``. After this runner moves the
    run to ``<output>/<Title>_<uid>/<timestamp>/`` those paths become stale.
    Only the run-dir prefix is rewritten; git-cache paths
    (``_github_repos_by_project/...``) never match ``<output>/<uid>/``.
    """
    if src_prefix == dst_prefix:
        return
    for json_path in target_dir.rglob('*.json'):
        try:
            text = json_path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        if src_prefix not in text:
            continue
        json_path.write_text(text.replace(src_prefix, dst_prefix), encoding='utf-8')

def run_job(job: Job, args: argparse.Namespace, status_path: Path, status_lock) -> dict[str, str]:
    target_dir = args.output_dir / job.title
    success_marker = target_dir / ".pipeline_success"
    log_path = args.output_dir / "_batch_logs" / f"local__{job.title}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    row = {"project_id": job.uid, "title": job.title, "source": job.source}

    if success_marker.exists() and not args.force and not args.dry_run:
        row.update(status="skipped", message="success marker exists", log=str(log_path))
        with status_lock:
            write_status(status_path, row)
        return row

    cmd = [
        args.python_bin, str(PIPELINE),
        "--project", job.uid,
        "--submissions-json", str(job.submissions_path),
        "--output-dir", str(args.output_dir),
        "--fix-script", str(args.fix_script),
        "--python-bin", args.python_bin,
        "--forge-bin", args.forge_bin,
        "--github-submodules", args.github_submodules,
        "--command-timeout", str(args.command_timeout),
        "--github-cache-dir", str(args.output_dir / "_github_repos_by_project" / job.uid),
        "--sleep", "0.05",
        "--api-workers", "1",
    ]
    if args.dry_run:
        cmd.append("--dry-run")
    if args.skip_flatten:
        cmd.append("--skip-flatten")
    if args.include_invalid:
        cmd.append("--include-invalid")
    for sev in args.severity or []:
        cmd.extend(["--severity", sev])

    started = time.time()
    with log_path.open("w", encoding="utf-8") as log_f:
        proc = subprocess.run(
            cmd, env=clean_env(), stdout=log_f, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
        )
    elapsed = int(time.time() - started)

    if proc.returncode == 0:
        row.update(status="success", message=f"pipeline exited 0 ({elapsed}s)", log=str(log_path))
        collect_uid_output(args.output_dir, job.uid, target_dir)
        if not args.dry_run:
            success_marker.parent.mkdir(parents=True, exist_ok=True)
            success_marker.write_text(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), encoding="utf-8")
    else:
        row.update(status="failed", message=f"pipeline exited {proc.returncode} ({elapsed}s)", log=str(log_path))

    with status_lock:
        write_status(status_path, row)
    return row


def write_status(path: Path, row: dict[str, str]) -> None:
    fieldnames = ["project_id", "title", "source", "status", "message", "log"]
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def main() -> int:
    args = parse_args()
    project_ids = args.project_ids or None
    if args.submissions_source == "reports":
        jobs = collect_report_jobs(args.reports_dir, args.output_dir, project_ids)
    else:
        jobs = collect_raw_dump_jobs(args.output_dir, project_ids)
    if not jobs:
        print("No projects found.")
        return 0
    print(f"Found {len(jobs)} projects from {args.submissions_source}.")
    start_at = max(1, args.start_at)
    end_at = len(jobs) if args.limit <= 0 else min(len(jobs), start_at - 1 + args.limit)
    selected = jobs[start_at - 1:end_at]
    print(f"Processing {len(selected)} projects (start_at={start_at}, limit={args.limit or 'none'}).")

    status_path = args.output_dir / "_batch_logs" / "local_reports_batch_status.csv"
    status_lock = threading.Lock()
    results: list[dict[str, str]] = []

    if len(selected) == 1 or args.jobs <= 1:
        for job in selected:
            print(f"RUN {job.title} ({job.uid})")
            results.append(run_job(job, args, status_path, status_lock))
    else:
        with ThreadPoolExecutor(max_workers=args.jobs) as ex:
            future_map = {ex.submit(run_job, job, args, status_path, status_lock): job for job in selected}
            for future in as_completed(future_map):
                results.append(future.result())

    success = sum(1 for r in results if r.get("status") == "success")
    failed = sum(1 for r in results if r.get("status") == "failed")
    skipped = sum(1 for r in results if r.get("status") == "skipped")
    print(f"\nBatch summary: success={success} failed={failed} skipped={skipped}")
    print(f"status: {status_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
