"""Evidence-grounded report elements and per-claim symbolic acceptance gates."""
import copy
import re

import report_only as r

ELEMENT_VERSION = 'report-elements/1'
FORMAL_VERSION = 'report-formalization/1'
KINDS = {'precondition', 'action', 'root_cause', 'impact', 'security_intent', 'assumption'}
MODALITIES = {'asserted', 'potential', 'inferred'}
ROLES = {'attacker', 'victim', 'authority', 'asset', 'contract', 'other'}


def require(condition, message):
    if not condition: raise ValueError(message)


def strings(value):
    return isinstance(value, list) and all(isinstance(x, str) for x in value)


def identifier(value):
    return isinstance(value, str) and re.fullmatch(r'[a-z][a-z0-9_]{0,63}', value)


def evidence_spans(quotes, text):
    require(strings(quotes) and bool(quotes), 'missing evidence quotes')
    spans = []
    for quote in quotes:
        require(bool(quote.strip()) and quote in text, 'evidence absent from input')
        # Record every occurrence; never silently disambiguate repeated evidence.
        starts, start = [], 0
        while True:
            pos = text.find(quote, start)
            if pos < 0: break
            starts.append(pos); start = pos + 1
        spans.append({'quote': quote, 'occurrences': [
            {'start': pos, 'end': pos + len(quote), 'line': text.count('\n', 0, pos) + 1}
            for pos in starts]})
    return spans


def index(items, label):
    require(isinstance(items, list) and len(items) <= 32, 'invalid ' + label)
    result = {}
    for item in items:
        require(isinstance(item, dict) and identifier(item.get('id')), 'invalid ' + label + ' id')
        require(item['id'] not in result, 'duplicate ' + label + ' id')
        result[item['id']] = item
    return result


def validate_elements(elements, text):
    require(isinstance(elements, dict) and set(elements) == {
        'schema_version', 'scope', 'entities', 'statements', 'attack_steps', 'ambiguities'},
        'unexpected elements fields')
    require(elements['schema_version'] == ELEMENT_VERSION, 'unknown elements schema')
    scope = elements['scope']
    require(isinstance(scope, dict) and set(scope) == {'flow', 'environment', 'evidence'}, 'invalid scope')
    require(all(isinstance(scope[k], str) and scope[k].strip() for k in ('flow', 'environment')), 'missing scope')
    evidence_spans(scope['evidence'], text)
    entities = index(elements['entities'], 'entity')
    statements = index(elements['statements'], 'statement')
    grounded = {'scope': evidence_spans(scope['evidence'], text), 'entities': {}, 'statements': {}}
    for name, entity in entities.items():
        require(set(entity) == {'id', 'name', 'role', 'evidence'}, 'unexpected entity fields')
        require(entity['role'] in ROLES and isinstance(entity['name'], str) and entity['name'].strip(), 'invalid entity')
        grounded['entities'][name] = evidence_spans(entity['evidence'], text)
    for name, statement in statements.items():
        require(set(statement) == {'id', 'kind', 'text', 'modality', 'entity_ids', 'evidence'}, 'unexpected statement fields')
        require(statement['kind'] in KINDS and statement['modality'] in MODALITIES, 'invalid kind/modality')
        require(isinstance(statement['text'], str) and statement['text'].strip(), 'missing statement text')
        require(strings(statement['entity_ids']) and all(x in entities for x in statement['entity_ids']), 'unknown entity reference')
        grounded['statements'][name] = evidence_spans(statement['evidence'], text)
    require(strings(elements['attack_steps']), 'invalid attack steps')
    require(len(set(elements['attack_steps'])) == len(elements['attack_steps']), 'duplicate attack step')
    require(all(x in statements and statements[x]['kind'] == 'action' for x in elements['attack_steps']), 'attack step must reference action')
    require(strings(elements['ambiguities']), 'invalid ambiguities')
    return grounded


def predicate_paths(expr, symbols, path=''):
    """Every Boolean operation/root must have an independently inspectable source."""
    result = []
    if expr is None: return result
    if path == '' or ('op' in expr and r.expr_type(expr, symbols) == ('bool', None)):
        result.append(path)
    for n, child in enumerate(expr.get('args', [])):
        result.extend(predicate_paths(child, symbols, (path + '.' if path else '') + f'args.{n}'))
    return result


def node_at(expr, path):
    if not path: return expr
    parts = path.split('.')
    require(len(parts) % 2 == 0, 'invalid formula path')
    for n in range(0, len(parts), 2):
        require(parts[n] == 'args' and parts[n + 1].isdigit(), 'invalid formula path')
        require(isinstance(expr, dict) and 'args' in expr, 'formula path absent')
        offset = int(parts[n + 1])
        require(offset < len(expr['args']), 'formula path absent')
        expr = expr['args'][offset]
    return expr


def validate_formalization(formal, elements, text):
    validate_elements(elements, text)
    require(isinstance(formal, dict) and set(formal) == {'schema_version', 'symbols', 'claims', 'limitations'}, 'unexpected formalization fields')
    require(formal['schema_version'] == FORMAL_VERSION, 'unknown formalization schema')
    require(strings(formal['limitations']), 'invalid limitations')
    require(isinstance(formal['symbols'], dict), 'invalid symbols')
    entities = index(elements['entities'], 'entity')
    statements = index(elements['statements'], 'statement')
    symbol_base = {}
    for name, item in formal['symbols'].items():
        require(isinstance(item, dict) and set(item) == {'sort', 'unit', 'meaning', 'checkpoint', 'evidence', 'entity_ids'}, 'unexpected observable fields')
        require(strings(item['entity_ids']) and all(x in entities for x in item['entity_ids']), 'unknown observable entity')
        symbol_base[name] = {k: v for k, v in item.items() if k != 'entity_ids'}
    claims = index(formal['claims'], 'claim')
    require(len(claims) <= 8, 'too many claims')
    claimed_impacts = set()
    for claim in claims.values():
        require(set(claim) == {'id', 'scope', 'modality', 'impact_ids', 'properties', 'formula_sources', 'effect_coverage', 'assumptions', 'unresolved'}, 'unexpected claim fields')
        require(isinstance(claim['scope'], str) and claim['scope'].strip(), 'missing claim scope')
        require(claim['modality'] in MODALITIES, 'invalid claim modality')
        require(strings(claim['impact_ids']) and all(x in statements and statements[x]['kind'] == 'impact' for x in claim['impact_ids']), 'invalid claim impacts')
        claimed_impacts.update(claim['impact_ids'])
        if any(statements[x]['modality'] == 'potential' for x in claim['impact_ids']):
            require(claim['modality'] == 'potential', 'potential impact upgraded to asserted effect')
        require(set(claim['properties']) == {'preconditions', 'safety', 'effects'}, 'unexpected properties')
        base_props = {}
        allowed = {'preconditions': {'precondition', 'assumption'},
                   'safety': {'security_intent'}, 'effects': {'impact'}}
        require(set(claim['formula_sources']) == set(allowed), 'unexpected formula source fields')
        for name, prop in claim['properties'].items():
            require(set(prop) == {'text', 'expression', 'evidence', 'derivation', 'source_ids'}, 'unexpected property fields')
            sources = prop['source_ids']
            require(strings(sources) and all(x in statements for x in sources), 'unknown property source')
            require(all(statements[x]['kind'] in allowed[name] for x in sources), 'property source role mismatch: ' + name)
            if prop['expression'] is not None:
                require(bool(sources), 'formal property missing source')
                if name == 'effects': require(set(sources) <= set(claim['impact_ids']), 'effect source outside claim')
                # Ground formula evidence in its own declared source, not just any report sentence.
                quotes = {q for x in sources for q in statements[x]['evidence']}
                require(set(prop['evidence']) <= quotes, 'property quote not linked to source')
            base_props[name] = {k: v for k, v in prop.items() if k != 'source_ids'}
            links = claim['formula_sources'][name]
            require(isinstance(links, dict), 'invalid formula sources')
            if prop['expression'] is None:
                require(not links, 'null property has formula paths')
                continue
            for path, ids in links.items():
                node_at(prop['expression'], path)
                require(strings(ids) and bool(ids) and set(ids) <= set(sources), 'invalid subformula sources')
            require(set(predicate_paths(prop['expression'], symbol_base)) <= set(links), 'predicate lacks source mapping')
        base = {'symbols': symbol_base, 'properties': base_props,
                'assumptions': claim['assumptions'], 'unresolved': claim['unresolved']}
        r.validate(base, text)
        coverage = index([dict(row, id=row.get('statement_id')) for row in claim['effect_coverage']], 'coverage')
        require(set(coverage) == set(claim['impact_ids']), 'impact coverage missing or duplicate')
        for row in claim['effect_coverage']:
            require(set(row) == {'statement_id', 'status', 'reason'}, 'unexpected coverage fields')
            require(row['status'] in ('formalized', 'partial', 'unformalized'), 'invalid coverage status')
            require(isinstance(row['reason'], str) and row['reason'].strip(), 'missing coverage reason')
            if row['status'] in ('formalized', 'partial'):
                require(base_props['effects']['expression'] is not None and row['statement_id'] in claim['properties']['effects']['source_ids'], 'coverage lacks effect expression/source')
    # Missing claims/impacts are reported, never silently equated with complete coverage.
    return symbol_base, claimed_impacts


def compile_bundle(elements, formal, text, strict_piv=False, verdict_v2=False):
    symbol_base, covered = validate_formalization(formal, elements, text)
    impacts = {x['id'] for x in elements['statements'] if x['kind'] == 'impact'}
    unassigned_preconditions = set()
    if strict_piv:
        extracted_preconditions = {x['id'] for x in elements['statements']
                                   if x['kind'] == 'precondition'}
        used_preconditions = {source for claim in formal['claims']
                              for source in claim['properties']['preconditions']['source_ids']
                              if source in extracted_preconditions}
        unassigned_preconditions = extracted_preconditions - used_preconditions
    output, warnings = [], []
    for claim in formal['claims']:
        base = {'symbols': symbol_base,
                'properties': {name: {k: v for k, v in prop.items() if k != 'source_ids'}
                               for name, prop in claim['properties'].items()},
                'assumptions': claim['assumptions'], 'unresolved': claim['unresolved']}
        validation, smt = r.compile_spec(base, text)
        relationship = r.relationship_review(base, text, require_direct_counterexample=strict_piv)
        reasons = list(validation['warnings']) + list(relationship['warnings'])
        # S12: under verdict_v2 a non-asserted modality is a *realization* fact, not
        # a structural defect, so it no longer blocks the positive verdict.
        if not verdict_v2 and claim['modality'] != 'asserted': reasons.append('claim is qualified or inferred; not a verified realized effect')
        # S12: coverage completeness is a bundle-level quality signal, not a
        # structural defect of one claim.
        coverage_partial = any(x['status'] != 'formalized' for x in claim['effect_coverage'])
        if not verdict_v2 and coverage_partial:
            reasons.append('claimed impact coverage is partial/unformalized')
        # S12: the model declaring per-claim limitations is honesty, not a defect.
        # The list itself stays in the claim output, so nothing is lost.
        if not verdict_v2 and claim['unresolved']:
            reasons.append('unresolved claim limitations require review')
        # S12: report-level ambiguities and formalization-level limitations are the
        # model's own honesty declarations.  Treating them as a global veto made a
        # positive verdict unreachable (measured: 0/74 claims ever passed).
        needs_review = bool(reasons) if verdict_v2 else (
            bool(reasons) or bool(elements['ambiguities']) or bool(formal['limitations']))
        status = validation['formalization_status']
        if status == 'formalized_candidate' and needs_review: status = 'needs_review'
        output.append({'id': claim['id'], 'formalization_status': status,
                       'structural_formalization_status': validation['formalization_status'],
                       'validation': validation, 'semantic_relationship': relationship,
                       'review_reasons': reasons, 'smt': smt, 'properties': copy.deepcopy(claim['properties']),
                       'formula_sources': copy.deepcopy(claim['formula_sources']),
                       'effect_coverage': copy.deepcopy(claim['effect_coverage']),
                       'scope': claim['scope'], 'modality': claim['modality'],
                       'assumptions': claim['assumptions'], 'unresolved': claim['unresolved']})
    # S12: coverage gaps are reported through coverage_status instead of vetoing
    # the whole bundle.  Measured as the single largest blocker (26/72 runs).
    if not verdict_v2 and impacts - covered:
        warnings.append('report impacts not assigned to a claim: ' + ', '.join(sorted(impacts - covered)))
    if not verdict_v2 and strict_piv and unassigned_preconditions:
        warnings.append('extracted preconditions not used by formal P: ' +
                        ', '.join(sorted(unassigned_preconditions)))
    if not verdict_v2 and elements['ambiguities']:
        warnings.append('report has declared ambiguities')
    if not verdict_v2 and formal['limitations']:
        warnings.append('formalization has declared limitations')
    core = 'formalized_candidate' if output and all(x['structural_formalization_status'] != 'not_formalized' for x in output) else 'partial'
    review = 'needs_review' if warnings or any(x['formalization_status'] != 'formalized_candidate' for x in output) else 'candidate_checks_passed'
    result = {'schema_version': 'stage2-semantic-bundle/1', 'core_formalization_status': core,
            'acceptance_status': review, 'report_warnings': warnings,
            'unassigned_impact_ids': sorted(impacts - covered), 'claims': output,
            'coverage_is_model_declared_not_semantically_verified': True,
            'human_semantic_review_required': True, 'code_alignment_status': 'not_attempted',
            'execution_ready': False, 'consistency_verdict': 'not_evaluated'}
    if verdict_v2:
        result['verdict_policy'] = 'signals-v2'
        result['report_ambiguities_declared'] = list(elements['ambiguities'])
        result['formalization_limitations_declared'] = list(formal['limitations'])
        gaps = []
        if impacts - covered: gaps.append('impacts_not_assigned')
        if strict_piv and unassigned_preconditions: gaps.append('preconditions_not_used')
        if any(row['status'] != 'formalized'
               for claim in output for row in claim['effect_coverage']):
            gaps.append('effect_coverage_partial')
        result['coverage_status'] = 'complete' if not gaps else 'partial'
        result['coverage_gaps'] = gaps
    if strict_piv:
        result['unassigned_precondition_ids'] = sorted(unassigned_preconditions)
        result['precondition_coverage_is_structural_not_semantic'] = True
        result['strict_piv_gate'] = True
    return result


# ======================================================================
# Normalization boundary (S13).
#
# Kept in this file on purpose: the stage-2 structure is frozen, and code
# serving one function lives in one file.  This belongs with the schema and
# gate validation above, which is what the boundary governs.
#
# Explicit normalization boundary for stage-2 model output.
#
# Why this module exists
# ----------------------
# The lib layer aborts a run from 228 distinct places (`require(...)` plus direct
# ``raise``), and before this module **none of them was classified**.  An
# unclassified boundary is not a boundary: it is a minefield where any single
# shape slip silently discards an otherwise correct run.  The gold-v1 blind run
# showed this directly -- `intuition_pause_escrow` died with
# ``invalid report-readiness fields`` although all four screening dimensions were
# present, correctly judged, and backed by real evidence IDs.
#
# The criterion
# -------------
# **Normalization may change how a fact is written down, never what is claimed.**
#
#     NORMALIZE  a mechanical fix preserves every semantic assertion
#                (position, naming, redundant telemetry, bookkeeping)
#     WARN       the claim is unchanged; only our confidence in it changes
#                (declared ambiguity / limitation / coverage gaps)
#     REJECT     fixing it would change what the P/I/V assert about the report
#
# Two layers, do not conflate them
# --------------------------------
# WARN is currently EMPTY *by design*.  The validators collected below only check
# whether a declaration is **well-formed**; a malformed declaration list is a
# shape error and stays REJECT.  The "declared uncertainty does not veto a claim"
# semantics already live one layer up, in ``semantic_core.compile_bundle`` under
# the ``signals`` verdict policy (S12).  Keeping them separate is what makes each
# layer testable on its own.
#
# Enforcement
# -----------
# ``tests/test_semantic_core.py`` re-derives every rejection point from
# the source with ``ast`` and fails if one is missing from ``BOUNDARY``.  The
# boundary therefore cannot drift silently when someone adds a ``require(...)``.
#
# No model call, no network, no artifact is read or written by this module.
# ======================================================================

NORMALIZE = 'normalize'
REJECT = 'reject'
WARN = 'warn'

#: ``(message, mode, note?)``.  Matched by exact equality first, then by prefix,
#: so dynamic messages such as ``f'unknown evidence ID {x}'`` (which the guard
#: test sees as the literal prefix ``'unknown evidence ID '``) also resolve.
#: Order matters only for prefix matches: NORMALIZE entries come first.
BOUNDARY = (
    # ---- NORMALIZE: a mechanical fix preserves every semantic assertion ----
    ('invalid report-readiness fields', NORMALIZE,
     'readiness telemetry nested one level too deep; hoisted by normalize_readiness()'),
    ('missing report-readiness summary', NORMALIZE,
     'readiness telemetry nested one level too deep; hoisted by normalize_readiness()'),

    # ---- REJECT: fixing these would change what the P/I/V claim ----
    ('P predicate symbol not grounded by its own source', REJECT),
    ('P predicate symbol not grounded by selected preconditions', REJECT),
    ('P term source not selected', REJECT),
    ('P terms must cover selected preconditions exactly once', REJECT),
    ('attack step must reference action', REJECT),
    ('bounded relation type/unit mismatch', REJECT),
    ('catalog does not match this report', REJECT),
    ('classified relation has no core observables', REJECT),
    ('classified relation uses unknown core observable', REJECT),
    ('conservation type/unit mismatch', REJECT),
    ('core relation observable has unknown source', REJECT),
    ('core relation observables lack intent/impact grounding', REJECT),
    ('correspondence type/unit mismatch', REJECT),
    ('coverage lacks effect expression/source', REJECT),
    ('derived definition target must be integer symbol', REJECT),
    ('derived definition type/unit mismatch', REJECT),
    ('derived definitions may reference base symbols only', REJECT),
    ('distinct P sources reuse identical predicate', REJECT),
    ('duplicate ', REJECT),
    ('duplicate attack step', REJECT),
    ('duplicate derived definition', REJECT),
    ('effect source outside claim', REJECT),
    ('empty conjunction', REJECT),
    ('empty disjunction', REJECT),
    ('empty report description/impact after filtering', REJECT),
    ('evidence absent from input', REJECT),
    ('expanded relation template mismatch', REJECT),
    ('fixed relation template mismatch', REJECT),
    ('formal property lacks evidence/derivation', REJECT),
    ('formal property missing source', REJECT),
    ('formula path absent', REJECT),
    ('impact context source not selected', REJECT),
    ('impact context symbol not grounded by its own source', REJECT),
    ('impact coverage missing or duplicate', REJECT),
    ('impact qualifier missing from formal plan: ', REJECT),
    ('invalid ', REJECT),
    ('invalid AST fields', REJECT),
    ('invalid ambiguities', REJECT),
    ('invalid arity', REJECT),
    ('invalid attack steps', REJECT),
    ('invalid authorization guard pattern', REJECT),
    ('invalid authorization pattern', REJECT),
    ('invalid bounded relation pattern', REJECT),
    ('invalid caveat list', REJECT),
    ('invalid claim impacts', REJECT),
    ('invalid claim modality', REJECT),
    ('invalid classified relation pattern', REJECT),
    ('invalid comparison binding', REJECT),
    ('invalid comparison types/units', REJECT),
    ('invalid compound predicate', REJECT),
    ('invalid condition pattern', REJECT),
    ('invalid conservation pattern', REJECT),
    ('invalid constant', REJECT),
    ('invalid correspondence pattern', REJECT),
    ('invalid coverage status', REJECT),
    ('invalid derived definition', REJECT),
    ('invalid derived definition sources', REJECT),
    ('invalid derived definitions', REJECT),
    ('invalid divisibility binding', REJECT),
    ('invalid divisibility type/unit', REJECT),
    ('invalid entity', REJECT),
    ('invalid exact power-of-two operand', REJECT),
    ('invalid formal plan', REJECT),
    ('invalid formula path', REJECT),
    ('invalid formula sources', REJECT),
    ('invalid impact context term', REJECT),
    ('invalid impact context terms', REJECT),
    ('invalid impact qualifier types', REJECT),
    ('invalid kind/modality', REJECT),
    ('invalid limitations', REJECT),
    ('invalid monotonicity pattern', REJECT),
    ('invalid plan P term', REJECT),
    ('invalid plan P terms', REJECT),
    ('invalid plan caveats', REJECT),
    ('invalid plan impact IDs', REJECT),
    ('invalid plan intent ID', REJECT),
    ('invalid plan precondition IDs', REJECT),
    ('invalid plan symbol', REJECT),
    ('invalid plan symbol entities', REJECT),
    ('invalid plan symbol sort', REJECT),
    ('invalid plan symbol sources', REJECT),
    ('invalid plan symbols', REJECT),
    ('invalid predicate binding', REJECT),
    ('invalid predicate operand', REJECT),
    ('invalid preservation pattern', REJECT),
    ('invalid property explanation', REJECT),
    ('invalid proportional relation pattern', REJECT),
    ('invalid quantity binding', REJECT),
    ('invalid quantity expression', REJECT),
    ('invalid quantity expression types', REJECT),
    ('invalid quantity relation', REJECT),
    ('invalid quantity relation types/units', REJECT),
    ('invalid relation obligation pattern', REJECT),
    ('invalid report-readiness decision', REJECT),
    ('invalid report-readiness dimension fields', REJECT),
    ('invalid report-readiness dimension status', REJECT),
    ('invalid report-readiness dimensions', REJECT),
    ('invalid report-readiness missing_dimensions', REJECT),
    ('invalid required effect pattern', REJECT),
    ('invalid scope', REJECT),
    ('invalid sort', REJECT),
    ('invalid structured unresolved blocking flag', REJECT),
    ('invalid structured unresolved category', REJECT),
    ('invalid structured unresolved item', REJECT),
    ('invalid structured unresolved list', REJECT),
    ('invalid structured unresolved sources', REJECT),
    ('invalid subformula sources', REJECT),
    ('invalid symbol count', REJECT),
    ('invalid symbols', REJECT),
    ('invalid temporal order pattern', REJECT),
    ('invalid truth binding', REJECT),
    ('invalid/deep AST', REJECT),
    ('invalid/duplicate evidence IDs', REJECT),
    ('invalid/reserved symbol name', REJECT),
    ('missing claim scope', REJECT),
    ('missing coverage reason', REJECT),
    ('missing evidence quotes', REJECT),
    ('missing plan quantity unit', REJECT),
    ('missing plan symbol semantics', REJECT),
    ('missing quantity unit', REJECT),
    ('missing report-readiness dimension must not cite evidence', REJECT),
    ('missing report-readiness reason', REJECT),
    ('missing scope', REJECT),
    ('missing statement text', REJECT),
    ('missing structured unresolved description', REJECT),
    ('missing symbol semantics', REJECT),
    ('model must return IDs, not quotes', REJECT),
    ('monotonicity type/unit mismatch', REJECT),
    ('non-quantity plan unit', REJECT),
    ('non-quantity unit', REJECT),
    ('null property has formula paths', REJECT),
    ('plan P source role mismatch', REJECT),
    ('plan symbol lacks evidence', REJECT),
    ('potential impact upgraded to asserted effect', REJECT),
    ('predicate lacks source mapping', REJECT),
    ('present report-readiness dimension lacks evidence', REJECT),
    ('property evidence absent from report', REJECT),
    ('property is not Boolean', REJECT),
    ('property quote not linked to source', REJECT),
    ('property source role mismatch: ', REJECT),
    ('proportional relation type/unit mismatch', REJECT),
    ('quantity expression requires integer', REJECT),
    ('recursive derived definition', REJECT),
    ('referenced derived symbol lacks definition', REJECT),
    ('relation alignment requires plan schema v3', REJECT),
    ('relation class and pattern mismatch', REJECT),
    ('relation repeats cancellable observable on both sides', REJECT),
    ('report JSON must be an object', REJECT),
    ('report JSON requires a nonempty body string', REJECT),
    ('report JSON title must be a nonempty string when present', REJECT),
    ('report-readiness decision/dimensions mismatch', REJECT),
    ('stage-2 DeepSeek API key is missing or malformed', REJECT),
    ('stage-2 DeepSeek key file missing; see config/stage2_deepseek.local.env.example', REJECT),
    ('stage-2 DeepSeek key file must be private (chmod 600)', REJECT),
    ('state preservation type/unit mismatch', REJECT),
    ('structured unresolved requires plan schema v2', REJECT),
    ('symbol evidence absent from report', REJECT),
    ('synthesized property is not Boolean', REJECT),
    ('temporal order type/unit mismatch', REJECT),
    ('too many claims', REJECT),
    ('tool use/model error; rejected', REJECT),
    ('trivial self-comparison predicate', REJECT),
    ('truth binding requires bool symbol', REJECT),
    ('type/unit mismatch', REJECT),
    ('unexpected claim fields', REJECT),
    ('unexpected coverage fields', REJECT),
    ('unexpected elements fields', REJECT),
    ('unexpected entity fields', REJECT),
    ('unexpected formal plan fields', REJECT),
    ('unexpected formalization fields', REJECT),
    ('unexpected formula source fields', REJECT),
    ('unexpected observable fields', REJECT),
    ('unexpected properties', REJECT),
    ('unexpected property fields', REJECT),
    ('unexpected statement fields', REJECT),
    ('unexpected symbol fields', REJECT),
    ('unknown ID elements schema', REJECT),
    ('unknown ID formalization schema', REJECT),
    ('unknown comparison symbol', REJECT),
    ('unknown correspondence symbol', REJECT),
    ('unknown elements schema', REJECT),
    ('unknown entity reference', REJECT),
    ('unknown evidence ID', REJECT),
    ('unknown formal plan schema', REJECT),
    ('unknown formalization schema', REJECT),
    ('unknown monotonicity symbol', REJECT),
    ('unknown observable entity', REJECT),
    ('unknown or duplicate report-readiness evidence ID', REJECT),
    ('unknown predicate symbol', REJECT),
    ('unknown preservation symbol', REJECT),
    ('unknown property source', REJECT),
    ('unknown relation class', REJECT),
    ('unknown report input policy version', REJECT),
    ('unknown report-readiness schema', REJECT),
    ('unknown synthesis pattern', REJECT),
    ('unknown temporal order symbol', REJECT),
    ('unsupported multiplication types', REJECT),
    ('unsupported official DeepSeek model identifier', REJECT),
    ('unsupported operator/types', REJECT),
    ('unsupported proxy : use "environment", "direct", or an http(s):// URL (urllib has no SOCKS support)', REJECT),

    # ---- transport failures: not a semantic boundary, still listed for coverage ----
    ('DeepSeek HTTP ; response body not saved', REJECT),
    ('DeepSeek JSON response must be an object', REJECT),
    ('DeepSeek network failure; details not saved', REJECT),
    ('DeepSeek response content missing', REJECT),
    ('DeepSeek response did not finish normally', REJECT),
    ('DeepSeek response envelope invalid; raw body not saved', REJECT),
    ('DeepSeek response exceeds local size limit', REJECT),
    ('model runtime exit ; category=; no fallback', REJECT),
)


def exact_entry_for(message):
    """The entry whose declared text equals this message exactly, or None.

    The coverage guard must use THIS, not ``entry_for``: prefix fallback would
    let a truncated entry keep "covering" the message it was meant to declare,
    which is how a boundary silently loses a point.
    """
    for entry in BOUNDARY:
        if entry[0] == message:
            return entry
    return None


def entry_for(message):
    """Entry governing this message: exact first, then declared-prefix fallback.

    The prefix pass exists for dynamic messages: an f-string such as
    ``f'unknown evidence ID {x}'`` is declared (and statically discovered) as the
    literal prefix ``'unknown evidence ID '``, which the runtime message extends.
    """
    entry = exact_entry_for(message)
    if entry is not None:
        return entry
    for entry in BOUNDARY:
        if message.startswith(entry[0]):
            return entry
    return None


def classify(message):
    """Mode for this rejection message; unlisted messages default to REJECT.

    The default is deliberately the historical behaviour, so an unclassified
    point can never silently start normalizing.
    """
    entry = entry_for(message)
    return entry[1] if entry else REJECT


def normalize_readiness(candidate):
    """Hoist readiness telemetry the model nested one level too deep.

    Observed on a real run: the response carried ``missing_dimensions`` and
    ``summary`` *inside* ``dimensions`` instead of beside it.  Every dimension
    was correct and ``decision`` was right, so this is a pure positional slip --
    moving the two keys up changes nothing the response asserts.

    Returns ``(candidate, changes)``; ``changes`` is empty when nothing applied.
    """
    if not isinstance(candidate, dict):
        return candidate, []
    dimensions = candidate.get('dimensions')
    if not isinstance(dimensions, dict):
        return candidate, []
    hoisted = {key: dimensions[key] for key in ('missing_dimensions', 'summary')
               if key not in candidate and key in dimensions}
    if not hoisted:
        return candidate, []
    normalized = {**candidate, **hoisted,
                  'dimensions': {key: value for key, value in dimensions.items()
                                 if key not in hoisted}}
    return normalized, [f'hoisted {key} out of dimensions' for key in hoisted]
