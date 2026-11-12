"""Stage-3 binding contracts and post-binding consistency ingestion.

semantic-live-5 (2026-10-08) additions, closing the missing stage-2 -> stage-3
loop described in ``docs/STAGE2_CURRENT_STATUS.md``:

- ``binding_contract``: a machine-checkable per-symbol contract embedded in
  ``stage3-spec.json``.  Report-only formulas over uninterpreted symbols have
  exactly as much checking power as stage 3's symbol binding; the contract
  turns that deferred interpretive burden into an explicit checklist (which
  symbols, which P/I/V roles, which binding kind) instead of prose hints.
- ``ingest_feedback``: stage 3 returns binding statuses and code-query
  results for one finished run; the feedback is validated against the run's
  own artifacts, the real ``consistency_verdict`` is computed, and
  ``stage3-consistency.json`` is written beside the run.  This is the first
  non-report adjudication of a derived invariant: code execution, not the
  report, decides whether the claimed violation is reachable.

Additive only.  No pipeline artifact is rewritten, ``verify`` keeps its
snapshot/feature replay contract, and the consistency file is written at most
once per run (re-ingestion of an already-adjudicated run is refused, mirroring
the "replay never overwrites" discipline).
"""
import json
from pathlib import Path

from lib import report_only as r
from lib.piv_contract import PIV_PROPERTY_BY_SYMBOL

#: interface role names, in the order stage 3 meets them in the SMT files.
ROLES = tuple((property_name, symbol)
              for symbol, property_name in PIV_PROPERTY_BY_SYMBOL.items())

#: query names stage 3 is expected to answer after building the code
#: transition T.  Mirrors ``code_queries_after_binding`` in stage3-spec.json.
CODE_QUERIES = ('P_and_T', 'P_and_T_and_not_I', 'P_and_T_and_V', 'P_and_T_and_not_V')

#: stage3-spec.json declares the queries in display form ("P AND T"); the
#: verdict logic (and this module) uses the canonical underscore form.  Real
#: stage-3 feedback may use either; ingest normalizes before adjudicating.
#: Regression: the first live smoke run died on exactly this mismatch.
QUERY_DISPLAY_ALIASES = {'P AND T': 'P_and_T',
                         'P AND T AND NOT I': 'P_and_T_and_not_I',
                         'P AND T AND V': 'P_and_T_and_V',
                         'P AND T AND NOT V': 'P_and_T_and_not_V'}


def _canonical_query(name):
    return QUERY_DISPLAY_ALIASES.get(name, name)

FEEDBACK_SCHEMA = 'stage3-consistency-feedback/1'
CONSISTENCY_SCHEMA = 'stage3-consistency/1'
BINDING_SCHEMA = 'stage3-binding-contract/1'
QUERY_STATUSES = ('sat', 'unsat', 'unknown')
BINDING_STATUSES = ('bound', 'unbound')


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _variables(expression):
    if expression is None:
        return set()
    if 'var' in expression:
        return {expression['var']}
    return set().union(*(_variables(child) for child in expression.get('args', []))) \
        if expression.get('args') else set()


def _binding_kind(sort):
    """What stage 3 must supply for one symbol, by its declared sort."""
    if sort == 'bool':
        return 'boolean_predicate'
    if sort == 'address':
        return 'address_value'
    return 'numeric_value'


def binding_contract(formal, claim):
    """The per-symbol binding checklist one claim hands to stage 3."""
    used = {role: _variables(claim['properties'][key]['expression'])
            for key, role in ROLES if claim['properties'].get(key)}
    symbols = []
    for name, item in formal['symbols'].items():
        appears_in = [role for _key, role in ROLES if name in used.get(role, set())]
        # New impact-level claims carry private symbol namespaces; omit other
        # claims' unused symbols from this handoff. Keep the historical
        # core_claim contract byte-stable for offline replay of old bundles.
        if claim['id'].startswith('impact_claim_') and not appears_in:
            continue
        symbols.append({
            'symbol': name,
            'sort': item['sort'],
            'unit': item['unit'],
            'meaning': item['meaning'],
            'checkpoint': item['checkpoint'],
            'entity_ids': item['entity_ids'],
            'appears_in': appears_in,
            'binding_kind': _binding_kind(item['sort']) if appears_in else 'not_required',
        })
    return {
        'schema_version': BINDING_SCHEMA,
        'claim_id': claim['id'],
        'roles': {role: key for key, role in ROLES},
        'symbols': symbols,
        'binding_rule': ('every symbol with appears_in nonempty must be bound to '
                         'a code-side observable before the code queries carry '
                         'meaning; bound observables must match sort/unit and the '
                         'cited checkpoint, never the report claim itself'),
    }


def _validate_feedback(feedback, spec, formal):
    _require(isinstance(feedback, dict), 'feedback must be an object')
    _require(set(feedback) <= {'schema_version', 'claim_id', 'symbol_bindings',
                               'code_query_results', 'poc'},
             'unexpected feedback fields')
    _require(feedback.get('schema_version') == FEEDBACK_SCHEMA,
             'unknown feedback schema version')
    claim_id = feedback.get('claim_id')
    declarations = spec.get('claims') or []
    _require(any(row.get('claim_id') == claim_id for row in declarations),
             'feedback names a claim absent from stage3-spec.json')
    claim = next(row for row in (formal.get('claims') or [])
                 if row.get('id') == claim_id)
    contract = binding_contract(formal, claim)
    required = {row['symbol'] for row in contract['symbols']
                if row['appears_in']}
    bindings = feedback.get('symbol_bindings')
    _require(isinstance(bindings, dict) and set(bindings) == required,
             'symbol_bindings must cover exactly the P/I/V symbols: ' +
             ','.join(sorted(required)))
    for name, row in bindings.items():
        _require(isinstance(row, dict) and set(row) <= {'status', 'binding'},
                 'invalid binding entry for ' + name)
        _require(row.get('status') in BINDING_STATUSES,
                 'invalid binding status for ' + name)
        _require(isinstance(row.get('binding'), str) and row['binding'].strip(),
                 'missing binding description for ' + name)
    results = feedback.get('code_query_results')
    allowed_queries = set(next(row['code_queries_after_binding'] for row in declarations
                               if row.get('claim_id') == claim_id))
    allowed_queries |= {_canonical_query(name) for name in allowed_queries}
    _require(isinstance(results, dict) and set(results) <= allowed_queries,
             'code_query_results must use the declared code queries')
    for name, status in results.items():
        _require(status in QUERY_STATUSES, 'invalid query status for ' + name)
    if 'poc' in feedback:
        poc = feedback['poc']
        _require(isinstance(poc, dict) and set(poc) <= {'executed', 'description'}
                 and type(poc.get('executed')) is bool and
                 isinstance(poc.get('description'), str) and poc['description'].strip(),
                 'invalid poc record')
    return contract


def consistency_verdict(contract, bindings, results):
    """Deterministic adjudication from the code-side query outcomes.

    The mapping is deliberately conservative: an unbound observable or an
    unknown solver answer never upgrades to a positive verdict, and
    ``P AND T`` infeasible flags the *binding* (a report-supported P that
    cannot hold on real code is far more likely a mis-binding than a refuted
    report) instead of silently counting as "invariant holds".

    The direct invariant contradiction (``P AND T AND NOT I``) is the primary
    consistency signal, mirroring KASC's oracle discipline of verifying the
    intended vulnerable behavior rather than trusting a passing test.
    ``P AND T AND V`` remains a corroborating witness when the direct query
    is unknown.
    """
    unbound = sorted(name for name, row in bindings.items()
                     if row['status'] != 'bound')
    if unbound:
        return 'partial_binding', unbound
    if results.get('P_and_T') == 'unsat':
        # P cannot hold on the bound code: suspect binding, not verdict.
        return 'preconditions_infeasible_on_code', unbound
    if results.get('P_and_T_and_not_I') == 'sat':
        return 'violation_reproduced', unbound
    if results.get('P_and_T_and_not_I') == 'unsat':
        # Invariant holds on code. A witnessed effect while the invariant
        # holds is an outcome mismatch: likely a vacuous/weak I or a
        # mis-binding, not proof of report-code agreement.
        if results.get('P_and_T_and_V') == 'sat':
            return 'effect_observed_invariant_holds', unbound
        return 'violation_not_reproduced', unbound
    if results.get('P_and_T_and_V') == 'sat':
        return 'violation_reproduced', unbound
    if results.get('P_and_T_and_V') == 'unsat':
        return 'violation_not_reproduced', unbound
    return 'inconclusive', unbound


def replan_diagnostic(record):
    """KASC-style outer-loop diagnostic from a consistency record.

    Every non-reproduced verdict carries an expected/observed/violated-gate
    triple plus the next bounded action, so an orchestrator can reroute to
    Stage-2 re-ruling or binding repair instead of terminating silently.
    """
    verdict = record.get('consistency_verdict')
    unbound = record.get('unbound_symbols', [])
    queries = record.get('code_query_results', {})
    base = {
        'schema_version': 'stage3-replan-diagnostic/1',
        'claim_id': record.get('claim_id'),
        'verdict': verdict,
        'unbound_symbols': unbound,
        'code_query_results': queries,
    }
    if verdict == 'violation_reproduced':
        return {**base, 'action': 'accept',
                'expected': 'report invariant is contradicted on code',
                'observed': 'P AND T AND NOT I is sat',
                'violated_gate': None}
    if verdict == 'violation_not_reproduced':
        return {**base, 'action': 'replan_rule',
                'expected': 'reported violation should reproduce on code',
                'observed': 'P AND T AND NOT I and P AND T AND V are unsat',
                'violated_gate': 'stage3_differential_not_reproduced',
                'hint': 'revisit Stage-2 I/V extraction or the PoC test range; '
                        'the invariant may be too weak or the PoC too narrow.'}
    if verdict == 'effect_observed_invariant_holds':
        return {**base, 'action': 'rebind_or_restate_i',
                'expected': 'observed effect should contradict the invariant',
                'observed': 'P AND T AND NOT I unsat while P AND T AND V sat',
                'violated_gate': 'stage3_outcome_mismatch',
                'hint': 'I may be vacuous or bound to the wrong observable.'}
    if verdict == 'preconditions_infeasible_on_code':
        return {**base, 'action': 'rebind',
                'expected': 'reported preconditions should hold on the bound code',
                'observed': 'P AND T is unsat',
                'violated_gate': 'stage3_preconditions_infeasible',
                'hint': 'check binding.json against the Stage-2 binding_contract.'}
    if verdict == 'partial_binding':
        return {**base, 'action': 'rebind',
                'expected': 'every appears_in symbol has a code binding',
                'observed': 'unbound: ' + ', '.join(unbound),
                'violated_gate': 'stage3_binding_incomplete',
                'hint': 'complete binding.json or rerun binding-skeleton.'}
    return {**base, 'action': 'collect_missing_evidence',
            'expected': 'all four code queries resolvable',
            'observed': 'one or more queries unknown',
            'violated_gate': 'stage3_inconclusive',
            'hint': 'collect missing forge traces or safety-path probe.'}


def ingest_feedback(directory, feedback):
    """Validate stage-3 feedback against a run and record its verdict."""
    directory = Path(directory)
    _require((directory / 'stage3-spec.json').is_file(), 'run has no stage3-spec.json')
    _require((directory / 'constraints.json').is_file(), 'run has no constraints.json')
    _require((directory / 'formalization.json').is_file(), 'run has no formalization.json')
    target = directory / 'stage3-consistency.json'
    _require(not target.exists(),
             'run already adjudicated; replay never overwrites a consistency record')
    spec = json.loads((directory / 'stage3-spec.json').read_text())
    formal = json.loads((directory / 'formalization.json').read_text())
    contract = _validate_feedback(feedback, spec, formal)
    # normalize display-form query names ("P AND T") to the canonical
    # underscore form the verdict logic reads.
    results = {_canonical_query(name): status for name, status
               in feedback.get('code_query_results', {}).items()}
    verdict, unbound = consistency_verdict(contract, feedback['symbol_bindings'], results)
    record = {
        'schema_version': CONSISTENCY_SCHEMA,
        'claim_id': feedback['claim_id'],
        'consistency_verdict': verdict,
        'unbound_symbols': unbound,
        'symbol_bindings': feedback['symbol_bindings'],
        'code_query_results': results,
        'poc': feedback.get('poc'),
        'binding_contract': contract,
        'adjudicated_by': 'stage3_code_execution',
        'adjudicates': 'the report-claimed invariant, not its translation fidelity',
        'model_calls': 0,
    }
    record['replan_diagnostic'] = replan_diagnostic(record)
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    return record
