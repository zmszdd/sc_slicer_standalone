#!/usr/bin/env python3
"""CLI wrapper for the locked evaluation contract."""
from __future__ import annotations

import sys
from pathlib import Path

STAGE3 = Path(__file__).resolve().parents[1]
if str(STAGE3) not in sys.path:
    sys.path.insert(0, str(STAGE3))

from lib.locked_eval import main  # noqa: E402


if __name__ == '__main__':
    raise SystemExit(main())
