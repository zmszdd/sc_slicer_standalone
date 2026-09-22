"""Schema tests for the pre-extraction semantic sufficiency gate."""
import unittest

from report_readiness import DIMENSIONS, validate_readiness


def catalog():
    return {'fragments': [{'id': f'e_{i}', 'text': str(i)} for i in range(1, 5)]}


def candidate(statuses=None):
    statuses = statuses or {name: 'present' for name in DIMENSIONS}
    dimensions = {}
    missing = []
    for index, name in enumerate(DIMENSIONS, 1):
        status = statuses[name]
        dimensions[name] = {
            'status': status,
            'evidence_ids': [f'e_{index}'] if status != 'missing' else [],
            'reason': 'supported' if status == 'present' else 'not sufficient',
        }
        if status != 'present':
            missing.append(name)
    return {
        'schema_version': 'report-readiness/1',
        'decision': 'ready' if not missing else 'insufficient',
        'dimensions': dimensions,
        'missing_dimensions': missing,
        'summary': 'input readiness decision',
    }


class ReportReadinessTests(unittest.TestCase):
    def test_all_dimensions_are_required(self):
        value = candidate()
        self.assertEqual(validate_readiness(value, catalog())['decision'], 'ready')
        statuses = {name: 'present' for name in DIMENSIONS}
        statuses['direct_effect'] = 'missing'
        value = candidate(statuses)
        self.assertEqual(validate_readiness(value, catalog())['decision'], 'insufficient')

    def test_unknown_evidence_is_rejected(self):
        value = candidate()
        value['dimensions']['affected_subject']['evidence_ids'] = ['unknown']
        with self.assertRaisesRegex(ValueError, 'evidence ID'):
            validate_readiness(value, catalog())

    def test_uncertainty_is_canonically_added_to_missing_dimensions(self):
        value = candidate()
        value['dimensions']['safety_relation_basis']['status'] = 'uncertain'
        value['decision'] = 'insufficient'
        checked = validate_readiness(value, catalog())
        self.assertEqual(checked['missing_dimensions'], ['safety_relation_basis'])


if __name__ == '__main__':
    unittest.main()
