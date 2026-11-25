"""Stage-3 -> Stage-2 bindability feedback contract.

``partial_binding`` and ``binding_error`` are not facts about a report; they
are a failed handoff from Stage-2 symbols to code observables.  This module
records where the handoff failed and asks the Stage-2 restatement gate for a
code-grounded rewrite.  It never converts an unresolved claim into a verdict.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

SCHEMA_VERSION = 'stage3-bindability-feedback/1'
FILE_NAME = 'bindability-feedback.json'


def build(claim_id: str, *, bindability: str | None = None,
          binding_record: dict | None = None,
          observable_ir: dict | None = None,
          unbound_report: dict | None = None,
          reference_patch: dict | None = None) -> dict:
    record = binding_record if isinstance(binding_record, dict) else {}
    ir = observable_ir if isinstance(observable_ir, dict) else {}
    report = unbound_report if isinstance(unbound_report, dict) else {}
    unbound = [str(name) for name in (record.get('unbound') or [])
               if str(name)]
    unresolved = [str(name) for name in (report.get('unresolved') or [])
                  if str(name)]
    invisible = []
    for symbol, row in (ir.get('symbols') or {}).items():
        if not isinstance(row, dict):
            continue
        candidates = row.get('candidates') or []
        if candidates and not any(item.get('visible_at_injection')
                                  for item in candidates
                                  if isinstance(item, dict)):
            invisible.append(str(symbol))
    accepted_binding = (
        record.get('status') in {'bound', 'reused', 'reference_route'}
        and not unbound and not unresolved
    )
    needs_restatement = bool(
        unbound or unresolved
        or record.get('status') in {'failed', 'stale'}
        or record.get('verdict') in {'binding_error', 'partial_binding'}
        or (invisible and not accepted_binding))
    reasons = []
    if unbound:
        reasons.append('unbound P/I symbols: ' + ', '.join(sorted(unbound)))
    if unresolved:
        reasons.append('semantic UNBOUND: ' + ', '.join(sorted(unresolved)))
    if invisible and not accepted_binding:
        reasons.append('candidates invisible at patch target: '
                       + ', '.join(sorted(invisible)))
    if invisible and accepted_binding:
        reasons.append('accepted binding supersedes invisible IR candidates')
    if record.get('status') in {'failed', 'stale'}:
        reasons.append('binding status ' + str(record['status']))
    if reference_patch and reference_patch.get('accepted'):
        needs_restatement = False
        reasons.append('reference patch route accepted; no I restatement required')
    return {
        'schema_version': SCHEMA_VERSION,
        'claim_id': claim_id,
        'bindability': bindability or record.get('bindability') or 'unknown',
        'needs_restatement': bool(needs_restatement),
        'unbound_symbols': sorted(set(unbound + unresolved)),
        'invisible_symbols': sorted(set(invisible)),
        'patch_contract': ir.get('patch_contract'),
        'patch_functions': list(ir.get('patch_functions') or []),
        'reference_patch_accepted': bool((reference_patch or {}).get('accepted')),
        'reasons': reasons,
        'requested_route': ('stage2_code_grounded_restatement'
                            if needs_restatement else 'continue_stage3'),
    }


def build_index(rows: list[dict]) -> dict:
    return {
        'schema_version': SCHEMA_VERSION,
        'claims': {str(row['claim_id']): row for row in rows
                   if isinstance(row, dict) and row.get('claim_id')},
    }


def write(case_dir: Path, rows: list[dict]) -> Path:
    path = Path(case_dir) / FILE_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_index(rows), ensure_ascii=False,
                               indent=2) + '\n')
    return path


def load(case_dir: Path) -> dict:
    path = Path(case_dir) / FILE_NAME
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    if payload.get('schema_version') != SCHEMA_VERSION:
        return {}
    claims = payload.get('claims')
    return claims if isinstance(claims, dict) else {}


def apply_to_contract(contract: dict, feedback: dict | None) -> dict:
    """Block auto-assert when an unresolved bindability handoff is recorded."""
    feedback = feedback if isinstance(feedback, dict) else {}
    if not feedback.get('needs_restatement'):
        return copy.deepcopy(contract) if isinstance(contract, dict) else {}
    result = copy.deepcopy(contract) if isinstance(contract, dict) else {}
    restatement = result.get('invariant_restatement') or {}
    resolved = (bool(restatement.get('accepted'))
                and str(restatement.get('status')) == 'restated'
                and bool(restatement.get('changes')))
    if resolved:
        return result
    result['status'] = 'needs_review'
    result['route'] = 'binding_review'
    result['can_auto_assert'] = False
    result['auto_assert_allowed'] = False
    result['contract_source'] = 'stage3_bindability_feedback'
    result.setdefault('problems', []).append({
        'code': 'BINDABILITY_FEEDBACK_UNRESOLVED',
        'severity': 'blocking',
        'message': '; '.join(feedback.get('reasons') or [])
        or 'stage-3 requested a code-grounded invariant restatement',
    })
    result['bindability_feedback'] = copy.deepcopy(feedback)
    return result
