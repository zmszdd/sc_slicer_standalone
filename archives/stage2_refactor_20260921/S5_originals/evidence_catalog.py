"""Deterministic source IDs; resolution never rewrites or fuzzy-matches a quote."""
import copy

import report_only as r
from semantic_core import require, strings


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
