"""Submit stage-3 feedback to phase-2's deterministic ingestion."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # repo root
STAGE2_DIR = ROOT / 'tools' / 'report_constraints_v2'


def submit(stage2_dir: Path, feedback: dict) -> dict:
    """Run phase-2 ``ingest_feedback`` in its own interpreter/cwd.

    The phase-2 module imports ``lib.report_only`` relative to its own
    ``tools/report_constraints_v2`` package, so it must run with that cwd.
    ``ingest_feedback`` writes ``stage3-consistency.json`` into ``stage2_dir``
    and refuses to overwrite an existing adjudication.
    """
    stage2_dir = Path(stage2_dir)
    feedback_path = stage2_dir / 'stage3-consistency-feedback.json'
    feedback_path.write_text(
        json.dumps(feedback, ensure_ascii=False, indent=2) + '\n')
    script = (
        "import json, sys\n"
        "from pathlib import Path\n"
        "from lib.stage3_consistency import ingest_feedback\n"
        "directory = Path(sys.argv[1])\n"
        "feedback = json.loads(Path(sys.argv[2]).read_text())\n"
        "record = ingest_feedback(directory, feedback)\n"
        "print(json.dumps(record, ensure_ascii=False, indent=2))\n"
    )
    proc = subprocess.run(
        [sys.executable, '-c', script, str(stage2_dir), str(feedback_path)],
        capture_output=True, text=True, cwd=str(STAGE2_DIR))
    if proc.returncode != 0:
        raise RuntimeError(
            f'ingest_feedback failed: {proc.stderr.strip()[:800]}')
    return json.loads(proc.stdout)
