"""Explicit assistant AST control from reviewed Brix semantics, NOT model repair."""
import argparse
import copy
import json
from pathlib import Path

import report_only as r
from evidence_catalog import hydrate_elements, hydrate_formalization
from semantic_core import validate_formalization

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'results/semantic/brix_fee_ids_core_model_01'


def candidate():
    formal = copy.deepcopy(json.loads((SOURCE / 'formalization-ids.json').read_text()))
    claim = formal['claims'][0]
    # Reviewed obligation only: no fee-mismatch revert under the selected premise.
    del formal['symbols']['excess_tolerated']
    claim['properties']['safety'] = {
        'text': 'Under the in-scope buffered overpayment premise, payment excess alone must not cause '
                'the specified NotEnoughNative fee-mismatch revert.',
        'expression': {'op': 'not', 'args': [{'var': 'paynative_reverted'}]},
        'evidence_ids': ['e_5d2a1d54551d_0010', 'e_5d2a1d54551d_0012'],
        'derivation': 'Assistant-reviewed control: expresses the intended buffered-payment obligation '
                      'using the same specific failure observation as V, scoped by P. '
                      'No claim of full transaction success or exact refund.',
        'source_ids': ['si_buffered_design_intent']}
    claim['formula_sources']['safety'] = {'': ['si_buffered_design_intent']}
    claim['unresolved'].append('Assistant-derived control, not a new external model extraction; '
                               'code binding and complete helper/payment/revert semantics remain absent.')
    text = (SOURCE / 'extraction-input.txt').read_text()
    catalog = json.loads((SOURCE / 'evidence-catalog.json').read_text())
    elements = hydrate_elements(json.loads((SOURCE / 'elements-ids.json').read_text()), catalog, text)
    validate_formalization(hydrate_formalization(formal, catalog, text), elements, text)
    return formal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    value = candidate()
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'formalization-ids.json').write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    origin = {'candidate_origin': 'assistant_review', 'source_directory': str(SOURCE),
              'source_formalization_sha256': r.sha((SOURCE / 'formalization-ids.json').read_bytes()),
              'model_calls': 0, 'change': 'replace an undefined property flag with a reviewed observable AST',
              'note': 'Only a local expression control; not evidence of improved model accuracy'}
    (args.output / 'origin.json').write_text(json.dumps(origin, indent=2) + '\n')
    print(json.dumps(origin))


if __name__ == '__main__': main()
