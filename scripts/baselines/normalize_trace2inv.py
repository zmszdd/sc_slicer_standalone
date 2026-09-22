#!/usr/bin/env python3
"""Normalize packaged Trace2Inv evidence logs into benchmark JSON records."""

from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path


INVARIANT = re.compile(r"^Invariant:\s*(.+?)\s*$", re.IGNORECASE)
BENCHMARK = re.compile(r"^=+\s*benchmark\s+(.+?):\s*$", re.IGNORECASE)
EXPLOIT_TX = re.compile(r"^exploitTx:\s*(\S+)", re.IGNORECASE)
PROTECTION = re.compile(
    r"Successfully stops the exploit(?:\s+using\s+(.+?))?\s*$",
    re.IGNORECASE,
)
COUNT_PATTERNS = {
    "training_count": (
        re.compile(r"^len\(training set\):\s*(\d+)", re.IGNORECASE),
        re.compile(r"^trainingExecutionSet:\s*(\d+)", re.IGNORECASE),
    ),
    "testing_count": (
        re.compile(r"^len\(testing set\):\s*(\d+)", re.IGNORECASE),
        re.compile(r"^testingExecutionSet:\s*(\d+)", re.IGNORECASE),
    ),
}


def parse_fp_map(line: str) -> list[str] | None:
    if not line.startswith("FPMap:"):
        return None
    value = line.split(":", 1)[1].strip()
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return []
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


def parse_log(path: Path) -> list[dict[str, object]]:
    category = path.stem
    records: list[dict[str, object]] = []
    current: dict[str, object] | None = None

    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        invariant_match = INVARIANT.match(line)
        if invariant_match:
            category = invariant_match.group(1)
            continue

        benchmark_match = BENCHMARK.match(line)
        if benchmark_match:
            current = {
                "category": category,
                "benchmark": benchmark_match.group(1),
                "exploit_tx": None,
                "training_count": None,
                "testing_count": None,
                "fp_invariants": [],
                "exploit_protections": [],
                "source_file": path.name,
            }
            records.append(current)
            continue

        if current is None:
            continue

        exploit_match = EXPLOIT_TX.match(line)
        if exploit_match:
            current["exploit_tx"] = exploit_match.group(1)
            continue

        fp_map = parse_fp_map(line)
        if fp_map is not None:
            current["fp_invariants"] = fp_map
            continue

        protection_match = PROTECTION.search(line)
        if protection_match:
            protection = protection_match.group(1) or category
            protections = current["exploit_protections"]
            assert isinstance(protections, list)
            if protection not in protections:
                protections.append(protection)
            continue

        for field, patterns in COUNT_PATTERNS.items():
            for pattern in patterns:
                count_match = pattern.match(line)
                if count_match:
                    current[field] = int(count_match.group(1))
                    break

    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args()

    paths = sorted(args.input_dir.glob("*.txt"))
    if not paths:
        parser.error(f"no Trace2Inv .txt logs found in {args.input_dir}")

    records = [record for path in paths for record in parse_log(path)]
    if not records:
        parser.error(f"no benchmark records found in {args.input_dir}")

    categories = sorted({str(record["category"]) for record in records})
    exploit_transactions = {
        str(record["exploit_tx"])
        for record in records
        if record["exploit_tx"] is not None
    }
    protected_records = sum(bool(record["exploit_protections"]) for record in records)
    document = {
        "schema_version": 1,
        "tool": "Trace2Inv",
        "source_dir": str(args.input_dir),
        "summary": {
            "record_count": len(records),
            "categories": categories,
            "unique_exploit_transaction_count": len(exploit_transactions),
            "records_with_explicit_exploit_protection": protected_records,
        },
        "records": records,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"normalized {len(records)} records across {len(categories)} categories "
        f"to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
