"""Validate and merge report-grounded statements from explicit Impact areas."""

import copy
import re


SCHEMA_VERSION = 'report-impact-inventory/2'
LEGACY_SCHEMA_VERSION = 'report-impact-inventory/1'
MAX_IMPACTS = 16
_IDENTIFIER = re.compile(r'^[a-z][a-z0-9_]{0,63}$')
_MODALITIES = {'asserted', 'potential'}
_LEGACY_MODALITIES = _MODALITIES | {'inferred'}


def _normalized_source_text(value):
    """Normalize presentation-only Markdown while preserving source wording."""
    value = re.sub(r'^\s*(?:[-+*]\s+|\d+[.)]\s+)', '', value,
                   flags=re.MULTILINE)
    value = re.sub(r'\*\*(.*?)\*\*', r'\1', value, flags=re.DOTALL)
    value = re.sub(r'__(.*?)__', r'\1', value, flags=re.DOTALL)
    value = re.sub(r'`([^`\n]+)`', r'\1', value)
    return ' '.join(value.split())


def validate_impact_inventory(candidate, allowed_ids, evidence_catalog=None):
    """Validate Impact-only claims, including verbatim support for new inventories.

    Schema /1 remains replayable for frozen historical runs. Schema /2 requires
    every impact text to be a verbatim excerpt of its cited Impact fragments.
    """
    if not isinstance(candidate, dict) or set(candidate) != {
            'schema_version', 'impacts', 'ambiguities'}:
        raise ValueError('invalid Impact inventory fields')
    version = candidate['schema_version']
    if version not in (SCHEMA_VERSION, LEGACY_SCHEMA_VERSION):
        raise ValueError('unknown Impact inventory schema')
    if version == SCHEMA_VERSION and evidence_catalog is None:
        raise ValueError('Impact inventory v2 requires its evidence catalog')
    rows = candidate['impacts']
    if not isinstance(rows, list) or len(rows) > MAX_IMPACTS:
        raise ValueError('invalid Impact inventory count')
    if not isinstance(candidate['ambiguities'], list) or not all(
            isinstance(item, str) for item in candidate['ambiguities']):
        raise ValueError('invalid Impact inventory ambiguities')
    allowed = set(allowed_ids)
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
                'id', 'text', 'modality', 'evidence_ids'}:
            raise ValueError('invalid Impact inventory item')
        if not isinstance(row['id'], str) or not _IDENTIFIER.fullmatch(row['id']):
            raise ValueError('invalid Impact inventory ID')
        if row['id'] in seen:
            raise ValueError('duplicate Impact inventory ID')
        seen.add(row['id'])
        if not isinstance(row['text'], str) or not row['text'].strip():
            raise ValueError('missing Impact inventory text')
        allowed_modalities = (_MODALITIES if version == SCHEMA_VERSION
                              else _LEGACY_MODALITIES)
        if row['modality'] not in allowed_modalities:
            raise ValueError('invalid Impact inventory modality')
        ids = row['evidence_ids']
        if (not isinstance(ids, list) or not ids or
                not all(isinstance(item, str) for item in ids) or
                len(set(ids)) != len(ids)):
            raise ValueError('invalid Impact inventory evidence IDs')
        if not set(ids) <= allowed:
            raise ValueError('Impact inventory cites evidence outside marked Impact areas')
        if version == SCHEMA_VERSION:
            fragments = {row['id']: row['text']
                         for row in evidence_catalog.get('fragments', [])}
            cited_text = _normalized_source_text(' '.join(
                fragments[item] for item in ids if item in fragments))
            quote = _normalized_source_text(row['text'])
            if not quote or quote not in cited_text:
                snippet = cited_text[:180] if cited_text else ''
                raise ValueError(
                    f"Impact inventory item '{row['id']}' text must quote "
                    'its cited Impact evidence verbatim; copy an exact '
                    f'continuous excerpt, e.g. {snippet!r}')
    if not allowed and rows:
        raise ValueError('Impact inventory requires an explicitly marked Impact area')
    return copy.deepcopy(candidate)


def repair_verbatim_texts(candidate, evidence_catalog=None):
    """Deterministically replace paraphrased impact text with verbatim excerpts.

    The v2 verbatim gate requires each impact's ``text`` to be an exact excerpt
    of its cited Impact fragments.  When a model paraphrases, the safest fix is
    not to keep retrying but to substitute the cited fragments' own wording, so
    the impact stays grounded and the gate passes deterministically.
    """
    if not isinstance(candidate, dict) or candidate.get('schema_version') != SCHEMA_VERSION:
        return None
    if not isinstance(evidence_catalog, dict):
        return None
    fragments = {row['id']: row['text']
                 for row in evidence_catalog.get('fragments', [])
                 if isinstance(row, dict)}
    if not fragments:
        return None
    value = copy.deepcopy(candidate)
    changed = False
    for row in value.get('impacts', []):
        if not isinstance(row, dict):
            return None
        ids = row.get('evidence_ids') or []
        if not ids or not all(isinstance(item, str) for item in ids):
            continue
        excerpt = _normalized_source_text(' '.join(
            fragments.get(item, '') for item in ids))
        if not excerpt:
            continue
        if _normalized_source_text(row.get('text') or '') != excerpt:
            row['text'] = excerpt
            changed = True
    return value if changed else None


def merge_impact_inventory(elements, inventory):
    """Inject the separately sourced impact inventory into report-elements/2."""
    value = copy.deepcopy(elements)
    if value.get('schema_version') != 'report-elements/2':
        raise ValueError('Impact inventory requires report-elements/2')
    statements = value.get('statements')
    if not isinstance(statements, list):
        raise ValueError('invalid core statement list')
    # The core pass has no authority to create impacts. Preserve its other roles
    # and use only the independently validated Impact-area inventory.
    statements[:] = [row for row in statements if row.get('kind') != 'impact']
    existing_ids = {row.get('id') for row in statements}
    for row in inventory['impacts']:
        if row['id'] in existing_ids:
            raise ValueError('duplicate statement ID across core and Impact inventory')
        existing_ids.add(row['id'])
        statements.append({
            'id': row['id'],
            'kind': 'impact',
            'text': row['text'],
            'modality': row['modality'],
            'entity_ids': [],
            'evidence_ids': list(row['evidence_ids']),
        })
    value['ambiguities'] = list(value.get('ambiguities', []))
    value['ambiguities'].extend(inventory['ambiguities'])
    return value
