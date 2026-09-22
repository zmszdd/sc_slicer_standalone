"""Frozen prompt implementations.

The historical files intentionally retain their original absolute imports and
bytes.  Adding this directory to ``sys.path`` lets those imports continue to
resolve after the files were moved out of the project root.
"""

from pathlib import Path
import sys

VERSION_DIR = str(Path(__file__).resolve().parent)
if VERSION_DIR not in sys.path:
    sys.path.insert(0, VERSION_DIR)
