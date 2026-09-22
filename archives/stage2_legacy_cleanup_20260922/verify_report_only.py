"""Read-only reproduction of a saved report-only candidate; no model calls."""
import argparse
import json
from pathlib import Path

import report_only as r


def verify(directory):
    spec = json.loads((directory / 'constraints.json').read_text())
    provenance = spec['provenance']
    report_bytes = (directory / 'report.json').read_bytes()
    report = json.loads(report_bytes)
    text = (directory / 'extraction-input.txt').read_text()
    assert r.sha(report_bytes) == provenance['report_sha256']
    assert r.sha(text.encode()) == provenance['report_input_sha256']
    if provenance.get('report_input_policy', {}).get('source_format') == 'report.json':
        version = provenance['report_input_policy'].get('policy_version')
        assert version in (None, 'report-json-input/2', 'report-json-input/3',
                           'report-json-input/4')
        current_policy = version is not None
        expected_text, expected_policy = r.report_json_input(
            report, deduplicate_title=current_policy,
            input_policy_version=int(version.rsplit('/', 1)[1]) if version else 2)
        assert provenance['report_input_policy'] == expected_policy
    else:
        # Historical outputs used body-only prose before the JSON allow-list.
        expected_text = r.prose_only(report['body'], resume_sections=False)
    assert text == expected_text
    for key in ('submission_uid', 'finding_uid'):
        assert report[key] == provenance[key]
    assert spec['schema_version'] == r.VERSION
    claim = {key: spec[key] for key in ('symbols', 'properties', 'assumptions', 'unresolved')}
    saved_path = directory / ('candidate.json' if provenance['replay_source'] else 'model-claim.json')
    assert json.loads(saved_path.read_text()) == claim
    result, smt = r.compile_spec(claim, text)
    assert result == spec['validation'] == json.loads((directory / 'status.json').read_text())
    assert smt == (directory / 'predicates.smt2').read_text()
    interface = json.loads((directory / 'stage3-spec.json').read_text())
    assert interface['constraints_sha256'] == r.sha((directory / 'constraints.json').read_bytes())
    assert interface['predicates_sha256'] == r.sha(smt.encode())
    assert interface['execution_ready'] is False
    return {'offline_verified': True, 'model_calls': 0, 'candidate_origin': provenance['candidate_origin'],
            'formalization_status': result['formalization_status'], 'consistency_verdict': 'not_evaluated'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    print(json.dumps(verify(parser.parse_args().directory), indent=2))
