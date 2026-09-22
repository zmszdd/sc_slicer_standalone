"""Preview exactly the local report prose selected for stage-2 model input.

No model call, no file writes. Check this output before authorizing a new source.
"""
import argparse
import json
from pathlib import Path
import sys

from semantic_pipeline import load_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--case-dir', type=Path)
    source.add_argument('--report', type=Path)
    args = parser.parse_args()
    text, _, provenance = load_report(case_dir=args.case_dir, report_path=args.report)
    print(json.dumps({
        'report_input_policy': provenance['report_input_policy'],
        'report_input_sha256': provenance['report_input_sha256'],
        'bytes': len(text.encode()),
        'external_model_called': False,
    }, ensure_ascii=False), file=sys.stderr)
    print(text)


if __name__ == '__main__':
    main()
