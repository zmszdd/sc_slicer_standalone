"""Print the exact lean second-step model DATA locally; never calls a model."""
import argparse
import json
from pathlib import Path

from evidence_catalog import build_catalog, hydrate_elements
from semantic_core import validate_elements
from semantic_pipeline import compact_json, lean_formal_input, load_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case-dir', type=Path, required=True)
    parser.add_argument('--elements', type=Path, required=True,
                        help='existing report-elements/2 JSON from the same case')
    args = parser.parse_args()
    text, _, _ = load_report(case_dir=args.case_dir)
    raw = json.loads(args.elements.read_text())
    if raw.get('schema_version') != 'report-elements/2':
        parser.error('lean preview requires report-elements/2')
    elements = hydrate_elements(raw, build_catalog(text), text)
    validate_elements(elements, text)
    print(compact_json(lean_formal_input(raw)))


if __name__ == '__main__':
    main()
