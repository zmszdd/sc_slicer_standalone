#!/usr/bin/env python3
"""Fetch and audit Code4rena reports for every project in the CSV.

The Code4rena data set has two different report sources:

* New live-judging projects expose reports through the Code4rena submissions API.
* Most historical projects publish the canonical reports in GitHub findings repos.

This script treats the CSV as authoritative, records per-project metadata, mirrors
all configured findings repos, fetches submissions API details when available, and
emits a coverage manifest that makes remaining gaps explicit.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
DEFAULT_DATA_DIR = ROOT / "data" / "code4rena"
DEFAULT_CSV_FILE = DEFAULT_DATA_DIR / "code4rena_audits_solidity_ended.csv"
DEFAULT_OUTPUT_DIR = ROOT / "code4rena_reports"
DEFAULT_CACHE_DIR = ROOT / ".code4rena_findings_cache"
DEFAULT_COOKIE_FILE = ROOT / ".code4rena_cookie"
DEFAULT_MANIFEST = DEFAULT_OUTPUT_DIR / "_coverage_manifest.json"
DEFAULT_GAPS_CSV = DEFAULT_OUTPUT_DIR / "_coverage_gaps.csv"
DEFAULT_REPO_QUEUE_CSV = DEFAULT_OUTPUT_DIR / "_repo_fetch_queue.csv"
DEFAULT_VERIFICATION_CSV = DEFAULT_OUTPUT_DIR / "_verification.csv"

LOG = logging.getLogger("fetch_code4rena_reports")


@dataclass
class RepoFetchResult:
    kind: str
    url: str
    status: str
    local_path: str | None = None
    file_count: int = 0
    error: str | None = None
    issues_status: str = "not_attempted"
    issues_path: str | None = None
    issue_count: int = 0
    comment_count: int = 0
    issues_error: str | None = None


def safe_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip()
    name = re.sub(r"\s+", " ", name)
    return name or "Unknown_Project"


def project_dir(output_dir: Path, row: dict[str, str]) -> Path:
    return output_dir / f"{safe_filename(row.get('title') or 'Unknown_Project')}_{row['project_id']}"


def find_report_files(path: Path) -> list[Path]:
    if not path.exists():
        return []
    names = {"report.md", "report.json"}
    return sorted(file for file in path.rglob("*") if file.is_file() and file.name in names)


def read_cookie(cookie_file: Path) -> str | None:
    value = os.environ.get("CODE4RENA_COOKIE", "").strip()
    if value:
        return value
    if cookie_file.exists():
        return cookie_file.read_text(encoding="utf-8").strip() or None
    return None


def requests_session(cookie: str | None, timeout_retry_total: int = 5, no_proxy: bool = False) -> requests.Session:
    session = requests.Session()
    if no_proxy:
        session.trust_env = False
    retries = Retry(
        total=timeout_retry_total,
        connect=timeout_retry_total,
        read=timeout_retry_total,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET"]),
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.headers.update(
        {
            "Accept": "application/json,text/plain,*/*",
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
            ),
        }
    )
    if cookie:
        session.headers["Cookie"] = cookie
    return session


def extract_submissions(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    data = payload.get("data")
    if isinstance(data, dict) and isinstance(data.get("submissions"), list):
        return [item for item in data["submissions"] if isinstance(item, dict)]
    if isinstance(payload.get("submissions"), list):
        return [item for item in payload["submissions"] if isinstance(item, dict)]
    for value in payload.values():
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def submission_number(item: dict[str, Any]) -> int | None:
    value = item.get("number")
    if str(value or "").isdigit():
        return int(value)
    return None


def extract_total_count(payload: Any) -> int | None:
    if not isinstance(payload, dict):
        return None
    candidates = [
        payload.get("total"),
        payload.get("totalCount"),
        payload.get("count"),
    ]
    for key in ["meta", "pagination", "pageInfo", "data"]:
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend([value.get("total"), value.get("totalCount"), value.get("count")])
    for value in candidates:
        if str(value or "").isdigit():
            return int(value)
    return None


def extract_payload_next_url(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    candidates = [
        payload.get("next"),
        payload.get("nextUrl"),
        payload.get("next_url"),
    ]
    for key in ["links", "pagination", "pageInfo", "meta"]:
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend([value.get("next"), value.get("nextUrl"), value.get("next_url")])
    for value in candidates:
        if isinstance(value, str) and value.startswith("http"):
            return value
    return None


def fetch_submission_listing(
    session: requests.Session,
    url: str,
    timeout: int,
    page_size: int = 100,
    max_pages: int = 200,
) -> dict[str, Any]:
    submissions_by_id: dict[int, dict[str, Any]] = {}
    page_summaries: list[dict[str, Any]] = []
    next_url: str | None = None
    total_count: int | None = None
    complete_listing = False
    maybe_truncated = False

    for page in range(1, max_pages + 1):
        params = None if next_url else {"page": page, "limit": page_size, "perPage": page_size}
        response = session.get(next_url or url, params=params, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
        submissions = extract_submissions(payload)
        page_ids = [number for item in submissions if (number := submission_number(item)) is not None]
        new_ids = [number for number in page_ids if number not in submissions_by_id]
        page_summaries.append(
            {
                "page": page,
                "url": response.url,
                "count": len(submissions),
                "ids": page_ids,
                "new_count": len(new_ids),
            }
        )

        for item in submissions:
            number = submission_number(item)
            if number is not None and number not in submissions_by_id:
                submissions_by_id[number] = item

        if total_count is None:
            total_count = extract_total_count(payload)

        header_next = response.links.get("next", {}).get("url") if response.links else None
        payload_next = extract_payload_next_url(payload)
        next_url = header_next or payload_next
        if next_url:
            continue

        if total_count is not None and len(submissions_by_id) >= total_count:
            complete_listing = True
            break
        if not submissions:
            complete_listing = True
            break
        if page > 1 and not new_ids:
            maybe_truncated = bool(page_summaries[0]["count"] >= 25)
            break
        if len(submissions) < 25:
            complete_listing = True
            break

    else:
        maybe_truncated = True

    remote_ids = sorted(submissions_by_id)
    return {
        "submissions": [submissions_by_id[number] for number in remote_ids],
        "remote_ids": remote_ids,
        "expected_count": total_count if total_count is not None else len(remote_ids),
        "page_summaries": page_summaries,
        "complete_listing": complete_listing,
        "maybe_truncated": maybe_truncated or not complete_listing,
    }


def legacy_submission_files(pdir: Path) -> list[Path]:
    return sorted(pdir.glob("submission_*.json"))


def submission_files(pdir: Path) -> list[Path]:
    return sorted(set(legacy_submission_files(pdir)) | set((pdir / "submissions_api").glob("submission_*.json")))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def has_repo_source(row: dict[str, str]) -> bool:
    return any(row.get(field, "").strip() for field in ["findingsRepo", "knownFindingsRepo", "botFindingsRepo"])


def fetch_submissions_api(
    session: requests.Session,
    row: dict[str, str],
    pdir: Path,
    timeout: int,
    sleep_seconds: float,
    audit_only: bool,
) -> dict[str, Any]:
    project_id = row["project_id"]
    url = f"https://code4rena.com/api/v1/audits/{project_id}/submissions"
    local_files = submission_files(pdir)
    result: dict[str, Any] = {
        "url": url,
        "status": "not_attempted",
        "expected_count": None,
        "remote_ids": [],
        "local_count": len(local_files),
        "local_ids": sorted(
            int(match.group(1))
            for path in local_files
            if (match := re.fullmatch(r"submission_(\d+)", path.stem))
        ),
        "missing_ids": [],
        "error": None,
    }
    if audit_only:
        result["status"] = "audit_only"
        return result

    try:
        listing = fetch_submission_listing(session, url, timeout)
    except requests.HTTPError as exc:
        result["status"] = "http_error"
        status_code = exc.response.status_code if exc.response is not None else "unknown"
        result["error"] = f"HTTP {status_code}"
        return result
    except Exception as exc:  # requests wraps proxy/DNS/SSL failures in several classes.
        result["status"] = "request_error"
        result["error"] = str(exc)
        return result

    submissions = listing["submissions"]
    remote_ids = listing["remote_ids"]
    result["status"] = "listed"
    result["expected_count"] = listing["expected_count"]
    result["remote_ids"] = remote_ids
    result["missing_ids"] = sorted(set(remote_ids) - set(result["local_ids"]))
    result["listing_complete"] = listing["complete_listing"]
    result["listing_maybe_truncated"] = listing["maybe_truncated"]
    result["page_count"] = len(listing["page_summaries"])

    write_json(
        pdir / "_submissions_index.json",
        {
            "url": url,
            "submissions": submissions,
            "page_summaries": listing["page_summaries"],
            "listing_complete": listing["complete_listing"],
            "listing_maybe_truncated": listing["maybe_truncated"],
            "expected_count": listing["expected_count"],
        },
    )
    detail_dir = pdir / "submissions_api"
    for sub_id in result["missing_ids"]:
        target = detail_dir / f"submission_{sub_id}.json"
        detail_url = f"{url}/{sub_id}"
        try:
            detail_response = session.get(detail_url, timeout=timeout)
        except Exception as exc:
            result.setdefault("detail_errors", []).append({"number": sub_id, "error": str(exc)})
            continue
        if detail_response.status_code != 200:
            result.setdefault("detail_errors", []).append(
                {"number": sub_id, "error": f"HTTP {detail_response.status_code}"}
            )
            continue
        try:
            detail = detail_response.json()
        except Exception as exc:
            result.setdefault("detail_errors", []).append({"number": sub_id, "error": str(exc)})
            continue
        write_json(target, detail)
        LOG.info("  saved API report: %s", target.relative_to(ROOT))
        time.sleep(sleep_seconds)

    refreshed = submission_files(pdir)
    result["local_count"] = len(refreshed)
    result["local_ids"] = sorted(
        int(match.group(1))
        for path in refreshed
        if (match := re.fullmatch(r"submission_(\d+)", path.stem))
    )
    result["missing_ids"] = sorted(set(remote_ids) - set(result["local_ids"]))
    if result["missing_ids"]:
        result["status"] = "incomplete"
    elif result.get("listing_maybe_truncated"):
        result["status"] = "maybe_truncated"
    elif remote_ids:
        result["status"] = "complete"
    return result


def normalize_repo_url(url: str) -> str:
    return url if url.endswith(".git") else f"{url}.git"


def repo_name(url: str) -> str:
    parsed = urlparse(url)
    name = Path(parsed.path).name
    return name.removesuffix(".git") or safe_filename(url)


def github_owner_repo(url: str) -> tuple[str, str] | None:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        return None
    return parts[0], parts[1].removesuffix(".git")


def run_git(args: list[str], cwd: Path | None, no_proxy: bool, timeout: int) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if no_proxy:
        for key in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
            env.pop(key, None)
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def copy_repo_worktree(src: Path, dst: Path) -> int:
    if dst.exists():
        shutil.rmtree(dst)
    ignore = shutil.ignore_patterns(".git")
    shutil.copytree(src, dst, ignore=ignore)
    return sum(1 for path in dst.rglob("*") if path.is_file())


def copy_archive_tree(src: Path, dst: Path) -> int:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    return sum(1 for path in dst.rglob("*") if path.is_file())


def archive_session(no_proxy: bool) -> requests.Session:
    session = requests.Session()
    if no_proxy:
        session.trust_env = False
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    session.headers.update({"User-Agent": "sc-slicer-code4rena-report-fetcher"})
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    return session


def github_default_branch(session: requests.Session, owner: str, repo: str, timeout: int) -> str | None:
    try:
        response = session.get(f"https://api.github.com/repos/{owner}/{repo}", timeout=timeout)
        if response.status_code != 200:
            return None
        payload = response.json()
    except Exception:
        return None
    branch = payload.get("default_branch") if isinstance(payload, dict) else None
    return branch if isinstance(branch, str) and branch else None


def count_existing_issues(path: Path) -> tuple[int, int]:
    issue_count = len(list((path / "issues").glob("issue_*.json"))) if (path / "issues").exists() else 0
    comment_count = (
        len(list((path / "comments").glob("issue_*_comments.json"))) if (path / "comments").exists() else 0
    )
    return issue_count, comment_count


def fetch_json_pages(session: requests.Session, url: str, timeout: int, params: dict[str, Any]) -> list[Any]:
    page = 1
    values: list[Any] = []
    while True:
        current_params = dict(params)
        current_params["page"] = page
        response = session.get(url, params=current_params, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise ValueError(f"expected list payload from {url}, got {type(payload).__name__}")
        values.extend(payload)
        if "next" not in response.links:
            return values
        page += 1


def fetch_github_issues(
    url: str,
    pdir: Path,
    kind: str,
    no_proxy: bool,
    timeout: int,
    include_comments: bool,
    audit_only: bool,
) -> dict[str, Any]:
    name = repo_name(url)
    issues_path = pdir / "github_issues" / kind / name
    existing_issue_count, existing_comment_count = count_existing_issues(issues_path)
    result: dict[str, Any] = {
        "status": "not_attempted",
        "path": str(issues_path),
        "issue_count": existing_issue_count,
        "comment_count": existing_comment_count,
        "error": None,
    }
    owner_repo = github_owner_repo(url)
    if not owner_repo:
        result["status"] = "bad_url"
        result["error"] = "not a GitHub owner/repo URL"
        return result
    if audit_only:
        result["status"] = "present" if existing_issue_count else "missing"
        return result

    owner, repo = owner_repo
    session = archive_session(no_proxy)
    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    try:
        issues = fetch_json_pages(session, api_url, timeout, {"state": "all", "per_page": 100})
        issues = [issue for issue in issues if isinstance(issue, dict) and "pull_request" not in issue]
        issue_dir = issues_path / "issues"
        comments_dir = issues_path / "comments"
        issue_dir.mkdir(parents=True, exist_ok=True)
        if include_comments:
            comments_dir.mkdir(parents=True, exist_ok=True)
        total_comments = 0
        for issue in issues:
            number = issue.get("number")
            if number is None:
                continue
            write_json(issue_dir / f"issue_{number}.json", issue)
            if include_comments and issue.get("comments_url"):
                comments = fetch_json_pages(session, issue["comments_url"], timeout, {"per_page": 100})
                write_json(comments_dir / f"issue_{number}_comments.json", comments)
                total_comments += len(comments)
        result["status"] = "complete"
        result["issue_count"] = len(issues)
        result["comment_count"] = total_comments
    except Exception as exc:
        result["status"] = "request_error"
        result["error"] = str(exc)
    return result


def attach_issue_result(repo_result: RepoFetchResult, issue_result: dict[str, Any]) -> RepoFetchResult:
    repo_result.issues_status = issue_result.get("status", "not_attempted")
    repo_result.issues_path = issue_result.get("path")
    repo_result.issue_count = int(issue_result.get("issue_count") or 0)
    repo_result.comment_count = int(issue_result.get("comment_count") or 0)
    repo_result.issues_error = issue_result.get("error")
    return repo_result


def mirror_findings_repo_archive(
    pdir: Path,
    kind: str,
    url: str,
    no_proxy: bool,
    timeout: int,
) -> RepoFetchResult:
    owner_repo = github_owner_repo(url)
    name = repo_name(url)
    dst = pdir / kind / name
    existing_count = sum(1 for path in dst.rglob("*") if path.is_file()) if dst.exists() else 0
    if not owner_repo:
        return RepoFetchResult(kind, url, "archive_bad_url", str(dst), existing_count, "not a GitHub owner/repo URL")

    owner, repo = owner_repo
    session = archive_session(no_proxy)
    errors: list[str] = []
    branches = []
    default_branch = github_default_branch(session, owner, repo, timeout)
    if default_branch:
        branches.append(default_branch)
    branches.extend(["main", "master"])
    for branch in dict.fromkeys(branches):
        archive_url = f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{branch}"
        tmp_zip = pdir / f".{name}.{branch}.zip.tmp"
        tmp_extract = pdir / f".{name}.{branch}.extract.tmp"
        try:
            response = session.get(archive_url, timeout=timeout)
            if response.status_code != 200:
                errors.append(f"{branch}: HTTP {response.status_code}")
                continue
            tmp_zip.write_bytes(response.content)
            if tmp_extract.exists():
                shutil.rmtree(tmp_extract)
            tmp_extract.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(tmp_zip) as archive:
                archive.extractall(tmp_extract)
            roots = [path for path in tmp_extract.iterdir() if path.is_dir()]
            if not roots:
                errors.append(f"{branch}: empty archive")
                continue
            file_count = copy_archive_tree(roots[0], dst)
            return RepoFetchResult(kind, url, "complete", str(dst), file_count)
        except Exception as exc:
            errors.append(f"{branch}: {exc}")
        finally:
            if tmp_zip.exists():
                tmp_zip.unlink()
            if tmp_extract.exists():
                shutil.rmtree(tmp_extract)
    return RepoFetchResult(kind, url, "archive_failed", str(dst), existing_count, "; ".join(errors))


def mirror_findings_repo(
    row: dict[str, str],
    pdir: Path,
    cache_dir: Path,
    kind: str,
    url: str,
    no_proxy: bool,
    git_timeout: int,
    archive_timeout: int,
    github_mode: str,
    audit_only: bool,
) -> RepoFetchResult:
    name = repo_name(url)
    dst = pdir / kind / name
    existing_count = sum(1 for path in dst.rglob("*") if path.is_file()) if dst.exists() else 0
    if audit_only:
        return RepoFetchResult(
            kind=kind,
            url=url,
            status="present" if existing_count else "missing",
            local_path=str(dst),
            file_count=existing_count,
        )

    if github_mode in {"archive", "auto"}:
        archive_result = mirror_findings_repo_archive(pdir, kind, url, no_proxy, archive_timeout)
        if archive_result.status == "complete" or github_mode == "archive":
            return archive_result

    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = cache_dir / name
    if cached.exists():
        proc = run_git(["-C", str(cached), "pull", "--ff-only"], None, no_proxy, git_timeout)
        if proc.returncode != 0:
            return RepoFetchResult(kind, url, "git_pull_failed", str(dst), existing_count, proc.stderr.strip())
    else:
        proc = run_git(["clone", "--depth", "1", normalize_repo_url(url), str(cached)], None, no_proxy, git_timeout)
        if proc.returncode != 0:
            prefix = ""
            if github_mode == "auto":
                prefix = f"archive fallback failed: {archive_result.error}; "
            return RepoFetchResult(kind, url, "git_clone_failed", str(dst), existing_count, prefix + proc.stderr.strip())

    try:
        file_count = copy_repo_worktree(cached, dst)
    except Exception as exc:
        return RepoFetchResult(kind, url, "copy_failed", str(dst), existing_count, str(exc))
    return RepoFetchResult(kind, url, "complete", str(dst), file_count)


def classify_project(
    row: dict[str, str], repo_results: list[RepoFetchResult], api_result: dict[str, Any], require_issues: bool
) -> str:
    required_repos = [row.get("findingsRepo"), row.get("knownFindingsRepo"), row.get("botFindingsRepo")]
    required_repos = [url for url in required_repos if url]
    if required_repos:
        repo_status_by_url = {result.url: result for result in repo_results}
        missing = [
            url
            for url in required_repos
            if repo_status_by_url.get(url) is None
            or repo_status_by_url[url].status not in {"complete", "present"}
            or repo_status_by_url[url].file_count == 0
            or (
                require_issues
                and repo_status_by_url[url].issues_status not in {"complete", "present"}
            )
        ]
        return "complete" if not missing else "incomplete_findings_repo"
    if api_result.get("status") == "complete":
        return "complete"
    if api_result.get("status") == "maybe_truncated":
        return "api_maybe_truncated"
    if api_result.get("local_count", 0) > 0 and api_result.get("status") in {"audit_only", "request_error", "http_error"}:
        return "api_cached_unverified"
    return "missing_source"


def process_project(args: argparse.Namespace, row: dict[str, str], session: requests.Session) -> dict[str, Any]:
    pdir = project_dir(args.output_dir, row)
    pdir.mkdir(parents=True, exist_ok=True)
    write_json(pdir / "_project.json", row)

    LOG.info("processing %s (%s)", row.get("title"), row["project_id"])
    repo_results: list[RepoFetchResult] = []
    for kind, field in [
        ("findings_repo", "findingsRepo"),
        ("known_findings_repo", "knownFindingsRepo"),
        ("bot_findings_repo", "botFindingsRepo"),
    ]:
        url = row.get(field, "").strip()
        if not url or args.skip_github:
            continue
        result = mirror_findings_repo(
            row=row,
            pdir=pdir,
            cache_dir=args.cache_dir,
            kind=kind,
            url=url,
            no_proxy=args.no_proxy,
            git_timeout=args.git_timeout,
            archive_timeout=args.archive_timeout,
            github_mode=args.github_mode,
            audit_only=args.audit_only,
        )
        if args.github_issues != "none":
            issue_result = fetch_github_issues(
                url=url,
                pdir=pdir,
                kind=kind,
                no_proxy=args.no_proxy,
                timeout=args.github_issues_timeout,
                include_comments=not args.skip_github_comments,
                audit_only=args.audit_only,
            )
            result = attach_issue_result(result, issue_result)
        repo_results.append(result)
        LOG.info(
            "  %s %s: %s (%s files), issues=%s (%s issues, %s comment files)",
            kind,
            url,
            result.status,
            result.file_count,
            result.issues_status,
            result.issue_count,
            result.comment_count,
        )

    api_result = {"status": "skipped", "local_count": len(submission_files(pdir))}
    should_query_api = args.api_scope == "all" or (args.api_scope == "without-repo" and not has_repo_source(row))
    if should_query_api:
        api_result = fetch_submissions_api(
            session=session,
            row=row,
            pdir=pdir,
            timeout=args.timeout,
            sleep_seconds=args.sleep,
            audit_only=args.audit_only,
        )
        LOG.info(
            "  submissions API: %s local=%s expected=%s",
            api_result.get("status"),
            api_result.get("local_count"),
            api_result.get("expected_count"),
        )

    coverage = classify_project(row, repo_results, api_result, require_issues=args.github_issues == "required")
    return {
        "project_id": row["project_id"],
        "title": row.get("title"),
        "audit_url": row.get("audit_url"),
        "auditType": row.get("auditType"),
        "status": row.get("status"),
        "codeAccess": row.get("codeAccess"),
        "schema": row.get("schema"),
        "languages": row.get("languages"),
        "mitigationOf": row.get("mitigationOf"),
        "project_dir": str(pdir),
        "coverage": coverage,
        "repos": [result.__dict__ for result in repo_results],
        "submissions_api": api_result,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_FILE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--gaps-csv", type=Path, default=DEFAULT_GAPS_CSV)
    parser.add_argument("--repo-queue-csv", type=Path, default=DEFAULT_REPO_QUEUE_CSV)
    parser.add_argument("--verification-csv", type=Path, default=DEFAULT_VERIFICATION_CSV)
    parser.add_argument("--cookie-file", type=Path, default=DEFAULT_COOKIE_FILE)
    parser.add_argument("--audit-only", action="store_true", help="only inspect local files; do not fetch network data")
    parser.add_argument("--skip-api", action="store_true", help="compatibility alias for --api-scope none")
    parser.add_argument("--skip-github", action="store_true", help="do not clone or update findings repos")
    parser.add_argument("--no-proxy", action="store_true", help="remove proxy env vars for git subprocesses")
    parser.add_argument(
        "--api-scope",
        choices=["without-repo", "all", "none"],
        default="without-repo",
        help="which projects should query the Code4rena submissions API",
    )
    parser.add_argument(
        "--only-gaps",
        action="store_true",
        help="read the current manifest and process only non-complete project ids",
    )
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--git-timeout", type=int, default=120)
    parser.add_argument("--archive-timeout", type=int, default=60)
    parser.add_argument(
        "--github-mode",
        choices=["auto", "archive", "clone"],
        default="auto",
        help="how to mirror GitHub findings repos; auto tries archive first then git clone",
    )
    parser.add_argument(
        "--github-issues",
        choices=["required", "optional", "none"],
        default="required",
        help="fetch GitHub issues for findings repos and optionally require them for coverage",
    )
    parser.add_argument("--github-issues-timeout", type=int, default=60)
    parser.add_argument("--skip-github-comments", action="store_true", help="fetch issues but not issue comments")
    parser.add_argument("--sleep", type=float, default=0.5)
    parser.add_argument("--limit", type=int, default=0, help="process only the first N CSV rows")
    parser.add_argument("--project-id", action="append", default=[], help="process only selected project ids")
    parser.add_argument("--log-file", type=Path, default=None)
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args(argv)


def configure_logging(args: argparse.Namespace) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if args.log_file:
        args.log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(args.log_file, encoding="utf-8"))
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )


def load_gap_project_ids(manifest: Path) -> set[str]:
    if not manifest.exists():
        return set()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    return {
        project["project_id"]
        for project in data.get("projects", [])
        if project.get("project_id") and project.get("coverage") != "complete"
    }


def load_manifest_projects(manifest: Path) -> list[dict[str, Any]]:
    if not manifest.exists():
        return []
    data = json.loads(manifest.read_text(encoding="utf-8"))
    return [project for project in data.get("projects", []) if project.get("project_id")]


def merge_project_results(
    previous_projects: list[dict[str, Any]], processed_projects: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if not previous_projects:
        return processed_projects
    processed_by_id = {project["project_id"]: project for project in processed_projects}
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for project in previous_projects:
        project_id = project["project_id"]
        merged.append(processed_by_id.get(project_id, project))
        seen.add(project_id)
    for project in processed_projects:
        if project["project_id"] not in seen:
            merged.append(project)
    return merged


def write_gap_csv(path: Path, projects: list[dict[str, Any]]) -> None:
    fields = [
        "coverage",
        "project_id",
        "title",
        "auditType",
        "status",
        "codeAccess",
        "schema",
        "mitigationOf",
        "api_status",
        "api_local_count",
        "api_expected_count",
        "api_page_count",
        "api_listing_maybe_truncated",
        "audit_url",
        "findings_repo",
        "known_findings_repo",
        "bot_findings_repo",
        "findings_issues_status",
        "known_issues_status",
        "bot_issues_status",
        "findings_issue_count",
        "known_issue_count",
        "bot_issue_count",
        "first_error",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for project in projects:
            if project.get("coverage") == "complete":
                continue
            repos = {repo.get("kind"): repo for repo in project.get("repos", [])}
            first_error = ""
            for repo in project.get("repos", []):
                if repo.get("error"):
                    first_error = repo["error"]
                    break
                if repo.get("issues_error"):
                    first_error = repo["issues_error"]
                    break
            if not first_error:
                first_error = project.get("submissions_api", {}).get("error") or ""
            writer.writerow(
                {
                    "coverage": project.get("coverage"),
                    "project_id": project.get("project_id"),
                    "title": project.get("title"),
                    "auditType": project.get("auditType"),
                    "status": project.get("status"),
                    "codeAccess": project.get("codeAccess"),
                    "schema": project.get("schema"),
                    "mitigationOf": project.get("mitigationOf"),
                    "api_status": project.get("submissions_api", {}).get("status"),
                    "api_local_count": project.get("submissions_api", {}).get("local_count"),
                    "api_expected_count": project.get("submissions_api", {}).get("expected_count"),
                    "api_page_count": project.get("submissions_api", {}).get("page_count"),
                    "api_listing_maybe_truncated": project.get("submissions_api", {}).get("listing_maybe_truncated"),
                    "audit_url": project.get("audit_url"),
                    "findings_repo": repos.get("findings_repo", {}).get("url", ""),
                    "known_findings_repo": repos.get("known_findings_repo", {}).get("url", ""),
                    "bot_findings_repo": repos.get("bot_findings_repo", {}).get("url", ""),
                    "findings_issues_status": repos.get("findings_repo", {}).get("issues_status", ""),
                    "known_issues_status": repos.get("known_findings_repo", {}).get("issues_status", ""),
                    "bot_issues_status": repos.get("bot_findings_repo", {}).get("issues_status", ""),
                    "findings_issue_count": repos.get("findings_repo", {}).get("issue_count", ""),
                    "known_issue_count": repos.get("known_findings_repo", {}).get("issue_count", ""),
                    "bot_issue_count": repos.get("bot_findings_repo", {}).get("issue_count", ""),
                    "first_error": first_error,
                }
            )


def write_repo_queue_csv(path: Path, projects: list[dict[str, Any]]) -> None:
    by_url: dict[str, dict[str, Any]] = {}
    for project in projects:
        for repo in project.get("repos", []):
            url = repo.get("url")
            if not url:
                continue
            entry = by_url.setdefault(
                url,
                {
                    "url": url,
                    "kind": repo.get("kind"),
                    "status": repo.get("status"),
                    "file_count": repo.get("file_count"),
                    "projects": [],
                    "titles": [],
                    "local_paths": [],
                    "error": repo.get("error") or "",
                    "issues_status": repo.get("issues_status"),
                    "issues_path": repo.get("issues_path") or "",
                    "issue_count": repo.get("issue_count") or 0,
                    "comment_count": repo.get("comment_count") or 0,
                    "issues_error": repo.get("issues_error") or "",
                },
            )
            entry["projects"].append(project.get("project_id"))
            entry["titles"].append(project.get("title"))
            if repo.get("local_path"):
                entry["local_paths"].append(repo["local_path"])
            if repo.get("status") not in {"complete", "present"}:
                entry["status"] = repo.get("status")
                entry["file_count"] = repo.get("file_count")
            if repo.get("error") and not entry.get("error"):
                entry["error"] = repo["error"]
            if repo.get("issues_error") and not entry.get("issues_error"):
                entry["issues_error"] = repo["issues_error"]
            if repo.get("issues_status") not in {"complete", "present"}:
                entry["issues_status"] = repo.get("issues_status")
                entry["issue_count"] = repo.get("issue_count") or 0
                entry["comment_count"] = repo.get("comment_count") or 0

    fields = [
        "status",
        "issues_status",
        "kind",
        "url",
        "file_count",
        "issue_count",
        "comment_count",
        "project_count",
        "projects",
        "titles",
        "local_paths",
        "error",
        "issues_error",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for entry in sorted(by_url.values(), key=lambda item: (item["status"] in {"complete", "present"}, item["url"])):
            writer.writerow(
                {
                    "status": entry.get("status"),
                    "issues_status": entry.get("issues_status"),
                    "kind": entry.get("kind"),
                    "url": entry.get("url"),
                    "file_count": entry.get("file_count"),
                    "issue_count": entry.get("issue_count"),
                    "comment_count": entry.get("comment_count"),
                    "project_count": len(entry["projects"]),
                    "projects": ";".join(filter(None, entry["projects"])),
                    "titles": ";".join(filter(None, entry["titles"])),
                    "local_paths": ";".join(entry["local_paths"]),
                    "error": entry.get("error", ""),
                    "issues_error": entry.get("issues_error", ""),
                }
            )


def verify_repo_result(repo: dict[str, Any]) -> dict[str, Any]:
    local_path = Path(repo.get("local_path") or "")
    issues_path = Path(repo.get("issues_path") or "")
    report_files = find_report_files(local_path)
    has_files = int(repo.get("file_count") or 0) > 0 and local_path.exists()
    has_issues = int(repo.get("issue_count") or 0) > 0 and issues_path.exists()
    has_report_file = bool(report_files)
    complete = has_files and repo.get("issues_status") in {"complete", "present"} and (has_issues or has_report_file)
    reasons = []
    if not has_files:
        reasons.append("repo_files_missing")
    if repo.get("issues_status") not in {"complete", "present"}:
        reasons.append("issues_missing")
    if not has_issues and not has_report_file:
        reasons.append("no_report_file_or_issue")
    return {
        "url": repo.get("url"),
        "kind": repo.get("kind"),
        "complete": complete,
        "has_files": has_files,
        "has_report_file": has_report_file,
        "report_file_count": len(report_files),
        "issue_count": int(repo.get("issue_count") or 0),
        "comment_count": int(repo.get("comment_count") or 0),
        "reasons": reasons,
    }


def verify_project(project: dict[str, Any]) -> dict[str, Any]:
    repos = project.get("repos", [])
    if repos:
        repo_checks = [verify_repo_result(repo) for repo in repos]
        complete = all(check["complete"] for check in repo_checks)
        reasons = sorted({reason for check in repo_checks for reason in check["reasons"]})
        return {
            "project_id": project.get("project_id"),
            "title": project.get("title"),
            "source_type": "github",
            "verified": complete,
            "reasons": reasons,
            "repo_count": len(repo_checks),
            "complete_repo_count": sum(1 for check in repo_checks if check["complete"]),
            "api_local_count": project.get("submissions_api", {}).get("local_count", 0),
            "repo_checks": repo_checks,
        }

    api = project.get("submissions_api", {})
    local_count = int(api.get("local_count") or 0)
    expected_count = api.get("expected_count")
    missing_ids = api.get("missing_ids") or []
    api_complete = api.get("status") == "complete" and local_count > 0 and not missing_ids
    cached_unverified = local_count > 0 and api.get("status") in {"audit_only", "request_error", "http_error"}
    reasons = []
    if not api_complete:
        if api.get("status") == "maybe_truncated":
            reasons.append("api_maybe_truncated")
        elif cached_unverified:
            reasons.append("api_cached_unverified")
        elif local_count == 0:
            reasons.append("api_reports_missing")
        elif expected_count is None:
            reasons.append("api_expected_count_unknown")
        elif missing_ids:
            reasons.append("api_missing_ids")
        else:
            reasons.append("api_not_complete")
    return {
        "project_id": project.get("project_id"),
        "title": project.get("title"),
        "source_type": "api",
        "verified": api_complete,
        "reasons": reasons,
        "repo_count": 0,
        "complete_repo_count": 0,
        "api_local_count": local_count,
        "api_expected_count": expected_count,
        "api_status": api.get("status"),
    }


def attach_verification(projects: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for project in projects:
        verification = verify_project(project)
        project["verification"] = verification
        key = "verified" if verification["verified"] else "unverified"
        counts[key] = counts.get(key, 0) + 1
        for reason in verification.get("reasons", []):
            reason_key = f"reason:{reason}"
            counts[reason_key] = counts.get(reason_key, 0) + 1
    return counts


def write_verification_csv(path: Path, projects: list[dict[str, Any]]) -> None:
    fields = [
        "verified",
        "project_id",
        "title",
        "source_type",
        "reasons",
        "repo_count",
        "complete_repo_count",
        "api_status",
        "api_local_count",
        "api_expected_count",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for project in projects:
            verification = project.get("verification") or verify_project(project)
            writer.writerow(
                {
                    "verified": verification.get("verified"),
                    "project_id": project.get("project_id"),
                    "title": project.get("title"),
                    "source_type": verification.get("source_type"),
                    "reasons": ";".join(verification.get("reasons") or []),
                    "repo_count": verification.get("repo_count"),
                    "complete_repo_count": verification.get("complete_repo_count"),
                    "api_status": verification.get("api_status", project.get("submissions_api", {}).get("status")),
                    "api_local_count": verification.get("api_local_count"),
                    "api_expected_count": verification.get("api_expected_count", project.get("submissions_api", {}).get("expected_count")),
                }
            )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.skip_api:
        args.api_scope = "none"
    configure_logging(args)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    previous_projects = load_manifest_projects(args.manifest) if args.only_gaps else []
    rows = list(csv.DictReader(args.csv.open(encoding="utf-8")))
    if args.project_id:
        selected = set(args.project_id)
        rows = [row for row in rows if row.get("project_id") in selected]
    if args.only_gaps:
        selected = load_gap_project_ids(args.manifest)
        if selected:
            rows = [row for row in rows if row.get("project_id") in selected]
        else:
            LOG.warning("--only-gaps requested but no existing gap manifest was found; processing all rows")
    if args.limit:
        rows = rows[: args.limit]

    cookie = read_cookie(args.cookie_file)
    session = requests_session(cookie, no_proxy=args.no_proxy)

    projects = []
    for row in rows:
        if not row.get("project_id"):
            continue
        projects.append(process_project(args, row, session))

    summary_projects = merge_project_results(previous_projects, projects) if args.only_gaps else projects
    summary: dict[str, Any] = {
        "csv": str(args.csv),
        "output_dir": str(args.output_dir),
        "total_projects": len(summary_projects),
        "coverage_counts": {},
        "verification_counts": {},
        "projects": summary_projects,
    }
    summary["verification_counts"] = attach_verification(summary_projects)
    for project in summary_projects:
        key = project["coverage"]
        summary["coverage_counts"][key] = summary["coverage_counts"].get(key, 0) + 1

    write_json(args.manifest, summary)
    write_gap_csv(args.gaps_csv, summary_projects)
    write_repo_queue_csv(args.repo_queue_csv, summary_projects)
    write_verification_csv(args.verification_csv, summary_projects)
    LOG.info("wrote manifest: %s", args.manifest)
    LOG.info("wrote gap csv: %s", args.gaps_csv)
    LOG.info("wrote repo queue csv: %s", args.repo_queue_csv)
    LOG.info("wrote verification csv: %s", args.verification_csv)
    LOG.info("coverage counts: %s", summary["coverage_counts"])
    LOG.info("verification counts: %s", summary["verification_counts"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
