"""Read a stage3-consistency.json and print its bounded re-plan diagnostic.

This is the outer-loop entry point: a non-reproduced verdict yields an
expected/observed/violated-gate triple plus the next bounded action, which an
orchestrator can use to reroute to Stage-2 re-ruling or binding repair.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description='Print the bounded re-plan diagnostic from a consistency record.')
    parser.add_argument('--consistency', required=True,
                        help='path to stage3-consistency.json')
    args = parser.parse_args()
    path = Path(args.consistency)
    if not path.is_file():
        print(json.dumps({'error': f'missing {path}'}), file=sys.stderr)
        return 2
    record = json.loads(path.read_text())
    diagnostic = record.get('replan_diagnostic')
    if diagnostic is None:
        diagnostic = {
            'schema_version': 'stage3-replan-diagnostic/1',
            'claim_id': record.get('claim_id'),
            'verdict': record.get('consistency_verdict'),
            'action': 'recompute_after_ingest',
            'expected': None,
            'observed': 'record predates replan_diagnostic',
            'violated_gate': 'stage3_replan_stale_record',
            'hint': 're-run stage3 to regenerate the diagnostic.',
        }
    print(json.dumps(diagnostic, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
