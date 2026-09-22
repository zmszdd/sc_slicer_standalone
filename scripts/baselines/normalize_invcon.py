#!/usr/bin/env python3
"""Normalize InvCon/Daikon program-point invariants into JSON records."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PROGRAM_POINT = re.compile(
    r"^(?P<contract>[A-Za-z_$][A-Za-z0-9_$]*)\."
    r"(?P<function>[^(:]+)(?P<signature>\([^)]*\)):::"
    r"(?P<phase>\S+)$"
)
STATE_VARIABLE = re.compile(r"\bthis\.([A-Za-z_$][A-Za-z0-9_$]*)")


def parse_invcon(text: str) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    current: dict[str, object] | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        match = PROGRAM_POINT.fullmatch(line)
        if match:
            current = {
                "contract": match.group("contract"),
                "function": match.group("function"),
                "signature": match.group("signature"),
                "phase": match.group("phase"),
                "program_point": line,
                "predicates": [],
            }
            records.append(current)
            continue

        if current is None or not line or set(line) == {"="}:
            continue

        predicates = current["predicates"]
        assert isinstance(predicates, list)
        predicates.append(line)

    for record in records:
        predicates = record["predicates"]
        assert isinstance(predicates, list)
        record["state_variables"] = sorted(
            {
                variable
                for predicate in predicates
                for variable in STATE_VARIABLE.findall(predicate)
            }
        )
        record["predicate_count"] = len(predicates)

    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="InvCon .inv file")
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args()

    records = parse_invcon(args.input.read_text(encoding="utf-8"))
    if not records:
        parser.error(f"no InvCon program points found in {args.input}")

    document = {
        "schema_version": 1,
        "tool": "InvCon",
        "source": str(args.input),
        "program_point_count": len(records),
        "predicate_count": sum(int(record["predicate_count"]) for record in records),
        "records": records,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"normalized {document['program_point_count']} program points and "
        f"{document['predicate_count']} predicates to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
