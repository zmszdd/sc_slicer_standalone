"""Stage-2 unit, replay, and evaluation regression tests."""
import sys
from pathlib import Path
_STAGE2 = Path(__file__).resolve().parent.parent
for _d in (_STAGE2 / 'lib', _STAGE2 / 'cli', _STAGE2):
    _s = str(_d)
    if _s not in sys.path:
        sys.path.insert(0, _s)

from lib import compat  # noqa: E402  (needs lib/ on sys.path first)

compat.install()
