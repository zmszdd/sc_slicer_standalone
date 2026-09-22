"""Evidence-grounded report sufficiency gate executed before P/I/V extraction."""
import copy
import json


SCHEMA_VERSION = 'report-readiness/1'
DIMENSIONS = (
    'affected_subject',
    'trigger_or_action',
    'direct_effect',
    'safety_relation_basis',
)
STATUSES = {'present', 'missing', 'uncertain'}

PROMPT = '''You are a conservative INPUT-SUFFICIENCY gate for vulnerability reports.
Do NOT extract P/I/V and do NOT judge whether the vulnerability is true. Decide only
whether the supplied numbered report fragments contain enough information for a later
model to derive a report-grounded P/I/V candidate.

Required dimensions:
1. affected_subject: identifiable affected component, function, state, asset, or actor.
2. trigger_or_action: a concrete triggering condition, operation, call, or state transition.
3. direct_effect: an immediate unauthorized behavior, state/value change, failed guarantee,
   or asset effect. Generic severity such as "fund loss is possible" alone is insufficient.
4. safety_relation_basis: evidence from which an expected-vs-actual, authorization,
   numeric, temporal, conservation, or state-transition safety relationship can be derived.
   The report need not explicitly say "invariant", but the relation must not be invented.

Use only supplied fragment IDs. A present dimension needs at least one supporting ID.
Missing dimensions use an empty evidence_ids list. Use uncertain when text hints at the
dimension but is too ambiguous to support a concrete relation. missing_dimensions MUST
list every dimension whose status is missing OR uncertain, in the required dimension
order. decision is ready only when all four dimensions are present; otherwise decision
is insufficient. Do not treat
PoC availability, code availability, severity labels, or a proposed fix as substitutes.
Return JSON only with exactly:
{"schema_version":"report-readiness/1","decision":"ready|insufficient",
 "dimensions":{
  "affected_subject":{"status":"present|missing|uncertain","evidence_ids":[],"reason":"short reason"},
  "trigger_or_action":{"status":"present|missing|uncertain","evidence_ids":[],"reason":"short reason"},
  "direct_effect":{"status":"present|missing|uncertain","evidence_ids":[],"reason":"short reason"},
  "safety_relation_basis":{"status":"present|missing|uncertain","evidence_ids":[],"reason":"short reason"}},
 "missing_dimensions":[],"summary":"short explanation"}
REPORT FRAGMENTS:\n'''


def model_payload(catalog):
    return json.dumps({
        'schema_version': catalog['schema_version'],
        'source_sha256': catalog['source_sha256'],
        'fragments': [{'id': row['id'], 'text': row['text']}
                      for row in catalog['fragments']],
    }, ensure_ascii=False, separators=(',', ':'))


def validate_readiness(candidate, catalog):
    if not isinstance(candidate, dict) or set(candidate) != {
            'schema_version', 'decision', 'dimensions', 'missing_dimensions', 'summary'}:
        raise ValueError('invalid report-readiness fields')
    if candidate['schema_version'] != SCHEMA_VERSION:
        raise ValueError('unknown report-readiness schema')
    if candidate['decision'] not in ('ready', 'insufficient'):
        raise ValueError('invalid report-readiness decision')
    dimensions = candidate['dimensions']
    if not isinstance(dimensions, dict) or set(dimensions) != set(DIMENSIONS):
        raise ValueError('invalid report-readiness dimensions')
    known_ids = {row['id'] for row in catalog['fragments']}
    not_present = []
    for name in DIMENSIONS:
        row = dimensions[name]
        if not isinstance(row, dict) or set(row) != {'status', 'evidence_ids', 'reason'}:
            raise ValueError('invalid report-readiness dimension fields')
        if row['status'] not in STATUSES:
            raise ValueError('invalid report-readiness dimension status')
        ids = row['evidence_ids']
        if (not isinstance(ids, list) or len(ids) != len(set(ids)) or
                any(not isinstance(item, str) or item not in known_ids for item in ids)):
            raise ValueError('unknown or duplicate report-readiness evidence ID')
        if row['status'] == 'present' and not ids:
            raise ValueError('present report-readiness dimension lacks evidence')
        if row['status'] == 'missing' and ids:
            raise ValueError('missing report-readiness dimension must not cite evidence')
        if not isinstance(row['reason'], str) or not row['reason'].strip():
            raise ValueError('missing report-readiness reason')
        if row['status'] != 'present':
            not_present.append(name)
    supplied_missing = candidate['missing_dimensions']
    if (not isinstance(supplied_missing, list) or
            any(item not in DIMENSIONS for item in supplied_missing)):
        raise ValueError('invalid report-readiness missing_dimensions')
    expected = 'ready' if not not_present else 'insufficient'
    if candidate['decision'] != expected:
        raise ValueError('report-readiness decision/dimensions mismatch')
    if not isinstance(candidate['summary'], str) or not candidate['summary'].strip():
        raise ValueError('missing report-readiness summary')
    # This is a deterministic projection of already validated statuses. Normalize
    # omission/order without changing a semantic judgment made by the model.
    candidate = copy.deepcopy(candidate)
    candidate['missing_dimensions'] = not_present
    return candidate
