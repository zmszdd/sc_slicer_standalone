"""Read-only replay of grounded semantic outputs and manifest hashes."""
import argparse
import json
from fidelity import check_numeric_plan, check_address_plan
from pathlib import Path

import report_only as r
from semantic_core import compile_bundle, require, validate_elements
from prompts.registry import (
    ADDRESS_GUARD_VERSIONS, ID_NORMALIZATION_VERSIONS,
    NUMERIC_GUARD_VERSIONS, PLAN_VERSIONS,
    PROTOCOL_IDENTIFIER_EXCLUSION_VERSIONS, RELATION_ALIGNMENT_VERSIONS,
    STRICT_PIV_VERSIONS, STRUCTURED_UNRESOLVED_VERSIONS,
)
from plan_synthesizer import (classified_relation_alignment, structured_unresolved_review,
                              synthesize_id_formalization)
from evidence_catalog import build_catalog, hydrate_elements, hydrate_formalization
from symbolic_queries import solve_queries, verify_witness
from review import attach_review
from mechanical_salvage import normalize_attack_step_roles, normalize_element_ids


def accepted_model_claim_path(directory):
    attempts_path = directory / 'formalization-attempts.json'
    if not attempts_path.exists():
        return directory / 'neural-formalization/model-claim.json'
    attempts = json.loads(attempts_path.read_text())
    accepted = [row for row in attempts if row.get('outcome') == 'accepted_for_validation']
    require(len(accepted) == 1, 'formalization attempt count mismatch')
    artifact_dir = accepted[0].get('artifact_dir')
    require(artifact_dir in {'neural-formalization', 'neural-formalization-retry-1',
                             'neural-formalization-retry-2'},
            'invalid formalization artifact directory')
    return directory / artifact_dir / 'model-claim.json'


def verify(directory):
    provenance = json.loads((directory / 'provenance.json').read_text())
    raw = (directory / 'original-report').read_bytes()
    require(r.sha(raw) == provenance['report_sha256'], 'report snapshot hash mismatch')
    text = (directory / 'extraction-input.txt').read_text()
    require(r.sha(text.encode()) == provenance['report_input_sha256'], 'prose hash mismatch')
    try:
        report = json.loads(raw)
        body = report['body']
    except json.JSONDecodeError:
        report = None
        body = raw.decode()
    policy = provenance.get('report_input_policy', {})
    if report is not None and policy.get('source_format') == 'report.json':
        version = policy.get('policy_version')
        require(version in (None, 'report-json-input/2', 'report-json-input/3',
                            'report-json-input/4'),
                'unknown report input policy')
        current_policy = version is not None
        expected_text, expected_policy = r.report_json_input(
            report, deduplicate_title=current_policy,
            input_policy_version=int(version.rsplit('/', 1)[1]) if version else 2)
        require(policy == expected_policy, 'report input policy changed')
    else:
        # Historical outputs predate the report.json title/body allow-list.
        require(policy.get('policy_version') in (None, 'legacy-prose/2', 'legacy-prose/3'),
                'unknown prose input policy')
        expected_text = r.prose_only(
            body, resume_sections=policy.get('policy_version') is not None,
            plain_section_exclusion=policy.get('policy_version') == 'legacy-prose/3')
    require(text == expected_text, 'prose not derived from saved report')
    elements = json.loads((directory / 'elements.json').read_text())
    require(validate_elements(elements, text) == json.loads((directory / 'evidence-spans.json').read_text()), 'evidence spans changed')
    formal = json.loads((directory / 'formalization.json').read_text())
    if (directory / 'evidence-catalog.json').exists():
        catalog = json.loads((directory / 'evidence-catalog.json').read_text())
        require(catalog == build_catalog(text), 'catalog mismatch')
        if (directory / 'elements-ids.json').exists():
            require(hydrate_elements(json.loads((directory / 'elements-ids.json').read_text()), catalog, text) == elements, 'ID element resolution mismatch')
        if (directory / 'formalization-ids.json').exists():
            require(hydrate_formalization(json.loads((directory / 'formalization-ids.json').read_text()), catalog, text) == formal, 'ID formal resolution mismatch')
    bundle = compile_bundle(elements, formal, text,
                            strict_piv=(provenance.get('prompt_version') in
                                        STRICT_PIV_VERSIONS))
    bundle['provenance'] = provenance
    saved = json.loads((directory / 'constraints.json').read_text())
    if 'observability_review' in saved:
        require(attach_review(bundle, formal) == json.loads((directory / 'observability-review.json').read_text()),
                'observability review replay mismatch')
    bundle['external_model_invocations'] = saved['external_model_invocations']
    for claim in bundle['claims']:
        require(claim.pop('smt') == (directory / (claim['id'] + '.smt2')).read_text(), 'SMT replay mismatch')
    require(bundle == saved, 'bundle replay mismatch')
    if provenance['candidate_origin'] == 'external_model':
        raw_elements = json.loads((directory / ('elements-ids.json' if (directory / 'elements-ids.json').exists() else 'elements.json')).read_text())
        raw_formal = json.loads((directory / ('formalization-ids.json' if (directory / 'formalization-ids.json').exists() else 'formalization.json')).read_text())
        if (directory / 'neural-elements/model-claim.json').exists():
            neural_elements = json.loads(
                (directory / 'neural-elements/model-claim.json').read_text())
            if (directory / 'element-format-normalization.json').exists():
                changes = []
                if provenance.get('prompt_version') in ID_NORMALIZATION_VERSIONS:
                    neural_elements, id_changes = normalize_element_ids(neural_elements)
                    changes.extend(id_changes)
                neural_elements, step_changes = normalize_attack_step_roles(neural_elements)
                changes.extend(step_changes)
                require(changes == json.loads(
                    (directory / 'element-format-normalization.json').read_text()),
                    'element normalization audit changed')
            require(neural_elements == raw_elements,
                    'neural elements changed')
        if provenance.get('prompt_version') in PLAN_VERSIONS:
            plan = json.loads((directory / 'formal-plan.json').read_text())
            require(json.loads(accepted_model_claim_path(directory).read_text()) == plan,
                    'neural formal plan changed')
            require(synthesize_id_formalization(plan, raw_elements) == raw_formal,
                    'deterministic formal synthesis changed')
            if provenance.get('prompt_version') in RELATION_ALIGNMENT_VERSIONS:
                require(classified_relation_alignment(plan, raw_elements) ==
                        json.loads((directory / 'relation-alignment.json').read_text()),
                        'classified relation alignment changed')
            if provenance.get('prompt_version') in NUMERIC_GUARD_VERSIONS:
                check_numeric_plan(
                    plan, raw_elements,
                    exclude_protocol_identifiers=(
                        provenance.get('prompt_version') in
                        PROTOCOL_IDENTIFIER_EXCLUSION_VERSIONS))
            if provenance.get('prompt_version') in ADDRESS_GUARD_VERSIONS:
                check_address_plan(plan, raw_elements)
            if provenance.get('prompt_version') in STRUCTURED_UNRESOLVED_VERSIONS:
                require(structured_unresolved_review(plan, raw_elements) ==
                        json.loads((directory / 'unresolved-review.json').read_text()),
                        'structured unresolved review changed')
        else:
            require(json.loads((directory / 'neural-formalization/model-claim.json').read_text()) == raw_formal,
                    'neural formulas changed')
    if (directory / 'solver-results.json').exists():
        solver_results = json.loads((directory / 'solver-results.json').read_text())['claims']
        require(set(solver_results) == {claim['id'] for claim in formal['claims']}, 'solver claim set mismatch')
        for claim in formal['claims']:
            base = {'symbols': {name: {k: v for k, v in item.items() if k != 'entity_ids'} for name, item in formal['symbols'].items()},
                    'properties': {name: {k: v for k, v in item.items() if k != 'source_ids'} for name, item in claim['properties'].items()},
                    'assumptions': claim['assumptions'], 'unresolved': claim['unresolved']}
            replay = solve_queries(base, text)
            require(set(replay) == set(solver_results[claim['id']]), 'solver query set mismatch')
            for name, result in solver_results[claim['id']].items():
                query_path = directory / result['path']
                require(query_path.resolve().is_relative_to(directory.resolve()), 'query path outside result directory')
                require(r.sha(query_path.read_bytes()) == result['sha256'], 'query hash mismatch')
                require(query_path.read_text() == replay[name]['smt'] and result['status'] == replay[name]['status'], 'query replay mismatch')
                if result['status'] == 'sat': verify_witness(base, name, result['witness'])
                else: require(result['witness'] is None, 'non-SAT query has witness')
    interface = json.loads((directory / 'stage3-spec.json').read_text())
    if 'observability_review_sha256' in interface:
        require(interface['observability_review_sha256'] == r.sha((directory / 'observability-review.json').read_bytes()),
                'interface observability review hash mismatch')
    if 'catalog_sha256' in interface:
        require(interface['catalog_sha256'] == r.sha((directory / 'evidence-catalog.json').read_bytes()), 'interface catalog hash mismatch')
    if 'solver_results_sha256' in interface:
        require(interface['solver_results_sha256'] == r.sha((directory / 'solver-results.json').read_bytes()), 'interface solver results hash mismatch')
    require(interface['spec_sha256'] == r.sha((directory / 'constraints.json').read_bytes()), 'interface spec hash mismatch')
    require(interface['elements_sha256'] == r.sha((directory / 'elements.json').read_bytes()), 'interface elements hash mismatch')
    for row in interface['claims']:
        require(row['predicates_sha256'] == r.sha((directory / row['predicates_path']).read_bytes()), 'interface SMT hash mismatch')
    require(interface['execution_ready'] is False, 'unexpected execution-ready claim')
    return {'offline_verified': True, 'model_calls': 0, 'candidate_origin': provenance['candidate_origin'],
            'core_formalization_status': bundle['core_formalization_status'],
            'acceptance_status': bundle['acceptance_status'], 'consistency_verdict': 'not_evaluated'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    print(json.dumps(verify(parser.parse_args().directory), indent=2))
