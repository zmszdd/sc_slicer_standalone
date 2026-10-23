"""Evidence-catalog + report-readiness ingestion layer.

合并自两个模块（S5），函数体逐字未改：
  - evidence_catalog.py : deterministic source IDs; resolution never rewrites or
                          fuzzy-matches a quote.
  - report_readiness.py : evidence-grounded report sufficiency gate executed before
                          P/I/V extraction.
"""
import copy
import json
import re

from lib import report_only as r
from lib.semantic_core import require, strings


# ------------------- 节选自 evidence_catalog.py -------------------

def build_catalog(text):
    digest = r.sha(text.encode())
    fragments, offset = [], 0
    for line in text.splitlines(keepends=True):
        for chunk_start in range(0, len(line), 700):
            start, end = offset + chunk_start, offset + min(chunk_start + 700, len(line))
            while start < end and text[start].isspace(): start += 1
            while end > start and text[end - 1].isspace(): end -= 1
            if start == end: continue
            fragments.append({'id': f'e_{digest[:12]}_{len(fragments) + 1:04d}',
                              'text': text[start:end], 'start': start, 'end': end,
                              'line': text.count('\n', 0, start) + 1})
        offset += len(line)
    return {'schema_version': 'report-evidence/1', 'source_sha256': digest, 'fragments': fragments}


_MARKDOWN_HEADING = re.compile(r'^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$')
_BOLD_HEADING = re.compile(r'^\s{0,3}(?:\*\*|__)(.+?)(?:\*\*|__)\s*:?[ \t]*$')
_INLINE_IMPACT = re.compile(
    r'^\s*(?:[-+*]\s+)?(?:\*\*|__)?\s*impact(?:\s+assessment)?\s*:'
    r'\s*(?:\*\*|__)?\s*(.*)$', re.IGNORECASE)


def _impact_heading_title(title):
    cleaned = re.sub(r'[`*_]', '', title).strip().rstrip(':').strip().lower()
    words = re.findall(r'[a-z]+', cleaned)
    return bool(words and (
        words[0] == 'impact' or words[-1] == 'impact' or
        ('impact' in words and any(word in words for word in
                                   ('finding', 'description', 'vulnerability')))))


def explicit_impact_ranges(text):
    """Return character ranges covered by explicitly labeled Impact areas.

    Supported forms include Markdown headings, standalone bold labels, combined
    "finding description and impact" headings, and inline ``Impact:`` labels.
    Unlabeled prose is never promoted into an Impact source range.
    """
    lines = []
    offset = 0
    for line in text.splitlines(keepends=True):
        lines.append((offset, offset + len(line), line))
        offset += len(line)
    ranges = []
    active_start = None
    active_level = None

    def close_section(end):
        nonlocal active_start, active_level
        if active_start is not None and end > active_start:
            ranges.append((active_start, end))
        active_start = None
        active_level = None

    for start, end, line in lines:
        content = line.rstrip('\r\n')
        heading = _MARKDOWN_HEADING.match(content)
        bold = _BOLD_HEADING.match(content)
        is_boundary = heading is not None or bold is not None
        if is_boundary:
            heading_level = (len(heading.group(0).lstrip().split(maxsplit=1)[0])
                             if heading else None)
            if (heading is not None and active_start is not None and
                    active_level is not None and
                    heading_level > active_level):
                # Subheadings within a marked combined area remain in scope;
                # the section ends at the next peer or parent heading.
                continue
            close_section(start)
            title = heading.group(1) if heading else bold.group(1)
            if _impact_heading_title(title):
                active_start = end
                active_level = heading_level
            continue
        inline = _INLINE_IMPACT.match(content)
        if inline:
            close_section(start)
            # The full source line remains the evidence fragment; the range
            # begins at the labeled content so adjacent prose is excluded.
            label_end = content.find(':') + 1
            body_start = start + label_end
            if content[label_end:].strip():
                ranges.append((body_start, end))
            else:
                active_start = end
            continue
        if active_start is not None and content.strip().startswith('->'):
            # Direct/Multi-User Impact sublabels belong to their parent section.
            continue
    close_section(len(text))
    return ranges


def explicit_impact_evidence_ids(catalog, text):
    """List evidence fragments overlapping explicitly marked Impact ranges."""
    require(catalog == build_catalog(text), 'catalog does not match this report')
    ranges = explicit_impact_ranges(text)
    return [row['id'] for row in catalog['fragments']
            if any(row['start'] < end and row['end'] > start
                   for start, end in ranges)]


def validate_impact_evidence(elements, allowed_ids):
    """Reject impact statements citing prose outside marked Impact areas."""
    allowed = set(allowed_ids)
    for row in elements.get('statements', []):
        if row.get('kind') != 'impact':
            continue
        ids = row.get('evidence_ids')
        require(isinstance(ids, list) and bool(ids),
                f"impact statement {row.get('id')} lacks Impact evidence")
        require(set(ids) <= allowed,
                f"impact statement {row.get('id')} cites evidence outside marked Impact areas")


def resolve(ids, catalog, text):
    require(catalog == build_catalog(text), 'catalog does not match this report')
    require(strings(ids) and bool(ids) and len(set(ids)) == len(ids), 'invalid/duplicate evidence IDs')
    index = {row['id']: row for row in catalog['fragments']}
    require(all(x in index for x in ids), 'unknown evidence ID')
    return [index[x]['text'] for x in ids]


def hydrate_elements(raw, catalog, text):
    require(isinstance(raw, dict) and raw.get('schema_version') == 'report-elements/2', 'unknown ID elements schema')
    value = copy.deepcopy(raw)
    value['schema_version'] = 'report-elements/1'
    for item in [value['scope']] + value['entities'] + value['statements']:
        require('evidence' not in item, 'model must return IDs, not quotes')
        item['evidence'] = resolve(item.pop('evidence_ids'), catalog, text)
    return value


def hydrate_formalization(raw, catalog, text):
    require(isinstance(raw, dict) and raw.get('schema_version') == 'report-formalization/2', 'unknown ID formalization schema')
    value = copy.deepcopy(raw)
    value['schema_version'] = 'report-formalization/1'
    for item in value['symbols'].values():
        require('evidence' not in item, 'model must return IDs, not quotes')
        quotes = resolve(item.pop('evidence_ids'), catalog, text)
        # Legacy observable schema takes one quote; all selected IDs remain in raw.
        item['evidence'] = quotes[0]
    for claim in value['claims']:
        for prop in claim['properties'].values():
            require('evidence' not in prop, 'model must return IDs, not quotes')
            ids = prop.pop('evidence_ids')
            prop['evidence'] = resolve(ids, catalog, text) if ids else []
    return value


# ------------------- 节选自 report_readiness.py -------------------
SCHEMA_VERSION = 'report-readiness/1'
DIMENSIONS = (
    'affected_subject',
    'trigger_or_action',
    'direct_effect',
    'safety_relation_basis',
)
STATUSES = {'present', 'missing', 'uncertain'}

PROMPT = '''You are a conservative REPORT-NARRATIVE-SUFFICIENCY gate for vulnerability reports.
Do NOT extract P/I/V and do NOT judge whether the vulnerability is true. Decide only
whether the supplied numbered report fragments explain the affected subject, trigger,
direct effect, and safety-relation basis well enough to attempt P/I/V formalization.
"ready" means only that the narrative is sufficient to try. It does not mean the
current rule grammar can express the relation, that numeric variables and units are
available, or that a model will successfully generate complete formulas. Those are
judged separately from the subsequent per-impact formalization results.

Required dimensions:
1. affected_subject: identifiable affected component, function, state, asset, or actor.
2. trigger_or_action: a concrete triggering condition, operation, call, or state transition.
3. direct_effect: an immediate unauthorized behavior, state/value change, failed guarantee,
   or asset effect. Generic severity such as "fund loss is possible" alone is insufficient.
4. safety_relation_basis: evidence from which an expected-vs-actual, authorization,
   numeric, temporal, conservation, or state-transition safety relationship can be derived.
   The report need not explicitly say "invariant". A NatSpec rule, quoted standard
   requirement, or mitigation that directly states expected behavior can support this
   dimension; implementation steps alone cannot. The relation must not be invented.

Use only supplied fragment IDs. A present dimension needs at least one supporting ID.
Missing dimensions use an empty evidence_ids list. Use uncertain when text hints at the
dimension but is too ambiguous to support a concrete relation. missing_dimensions MUST
list every dimension whose status is missing OR uncertain, in the required dimension
order. decision is ready only when all four dimensions are present; otherwise decision
is insufficient. A proposed fix may support only the safety-relation dimension when its
text directly states the expected property; it cannot replace evidence of the affected
subject, trigger, or direct effect. Do not treat PoC availability, code availability,
or severity labels as substitutes.
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
