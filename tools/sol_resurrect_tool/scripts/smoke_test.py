#!/usr/bin/env python3
"""Fast local smoke test for parser, assembler, and Foundry validation."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = TOOL_DIR.parents[1]
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

from main import _run_compile, _write_output
from src.assembler import Assembler
from src.parser import SolidityParser
from src.types import InferenceResult


SMOKE_SOURCE = b"""// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import 'forge-std/Test.sol';

contract PoC is Test {
    uint256 internal value;
}

function test_increment() public {
    value = 1;
    assertEq(value, 1);
}
"""


def main() -> int:
    output_dir = WORKSPACE_ROOT / "runs" / "sol_resurrect" / "smoke"
    output_path = output_dir / "ResurrectedSmoke.t.sol"
    if output_dir.exists():
        shutil.rmtree(output_dir)

    manifest = SolidityParser().parse(SMOKE_SOURCE)
    assert len(manifest.contracts) == 1, "expected one contract shell"
    assert len(manifest.orphans) == 1, "expected one orphan test function"

    inference = InferenceResult(rehoming_map={"test_increment": "PoC"})
    code = Assembler().assemble(manifest, inference)
    _write_output(str(output_path), code)

    ok, compiler_output, command = _run_compile(str(output_path), phase="smoke")
    if not ok:
        print("[FAIL] Smoke compile failed")
        print(f"command: {command}")
        print(compiler_output)
        return 1

    print("[PASS] Smoke test generated and compiled a minimal resurrected Foundry test")
    print(f"output: {output_path.relative_to(WORKSPACE_ROOT)}")
    print(f"command: {command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
