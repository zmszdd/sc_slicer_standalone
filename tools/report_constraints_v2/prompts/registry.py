"""Single registry for prompt versions and their supported pipeline features.

Keep version-specific prompt text in ``prompts/versions``.  Runtime code should
depend on this registry instead of importing every historical module itself.
"""

from importlib import import_module
from pathlib import Path

# Importing the package installs the frozen-version directory on sys.path.  The
# source files can therefore keep their historical absolute import statements.
from . import versions as _versions  # noqa: F401
from . import current as _current


MODULE_NAMES = (
    'semantic_prompts_v35',
    'semantic_prompts_v36',
    'semantic_prompts_v37',
    'semantic_prompts_v38',
    'semantic_prompts_v39',
    'semantic_prompts_v310',
    'semantic_prompts_v311',
    'semantic_prompts_v312',
    'semantic_prompts_v313',
    'semantic_prompts_v314',
    'semantic_prompts_v315',
    'semantic_prompts_v316',
    'semantic_prompts_v317',
    'semantic_prompts_v318',
    'semantic_prompts_v319',
    'semantic_prompts_v320',
)

MODULES = tuple(import_module(f'{__package__}.versions.{name}')
                for name in MODULE_NAMES)
PROMPT_MODULES = {module.PROMPT_VERSION: module for module in MODULES}
VERSIONS = tuple(PROMPT_MODULES)
# semantic-live-16 was the last single-I live schema. Keep its prompt and
# feature matrix immutable while the editable live prompt advances.
from . import live16_snapshot as _live16_snapshot
PROMPT_MODULES[_live16_snapshot.PROMPT_VERSION] = _live16_snapshot
# Preserve semantic-live-17 as a frozen replay target before advancing the
# editable live prompt. Historical runs retain their original feature matrix.
from . import live17_snapshot as _live17_snapshot
PROMPT_MODULES[_live17_snapshot.PROMPT_VERSION] = _live17_snapshot
# Preserve semantic-live-18 as an exact replay target before advancing the live prompt.
from . import live18_snapshot as _live18_snapshot
PROMPT_MODULES[_live18_snapshot.PROMPT_VERSION] = _live18_snapshot
# Preserve semantic-live-19's prompt-only experiment before the direct-V schema change.
from . import live19_snapshot as _live19_snapshot
PROMPT_MODULES[_live19_snapshot.PROMPT_VERSION] = _live19_snapshot
# Preserve semantic-live-20 before tightening source-role isolation and repair scope.
from . import live20_snapshot as _live20_snapshot
PROMPT_MODULES[_live20_snapshot.PROMPT_VERSION] = _live20_snapshot
# Preserve semantic-live-22 before advancing the active prompt with generation-
# side relation context and explicit vacuity checks.
from . import live22_snapshot as _live22_snapshot
PROMPT_MODULES[_live22_snapshot.PROMPT_VERSION] = _live22_snapshot
# Preserve semantic-live-23 before introducing a generated, audit-only bridge
# trace in the same rule-generation call.
from . import live23_snapshot as _live23_snapshot
PROMPT_MODULES[_live23_snapshot.PROMPT_VERSION] = _live23_snapshot
# Preserve semantic-live-24 before the unconditional-I prompt tightening.
from . import live24_snapshot as _live24_snapshot
PROMPT_MODULES[_live24_snapshot.PROMPT_VERSION] = _live24_snapshot
# Preserve semantic-live-25 before softening the pending-fallback wording.
from . import live25_snapshot as _live25_snapshot
PROMPT_MODULES[_live25_snapshot.PROMPT_VERSION] = _live25_snapshot
# Preserve semantic-live-26 before adding the observability contract.
from . import live26_snapshot as _live26_snapshot
PROMPT_MODULES[_live26_snapshot.PROMPT_VERSION] = _live26_snapshot
# ``VERSIONS`` contains only archived semantic-v3.x modules. The live-16
# snapshot is selectable for exact replay, but is not part of those frozen
# generation baselines or feature suffixes.

# Preserve the stable command-line alias while also exposing the live prompt's
# stamped revision for frozen evaluation manifests. Both names resolve to the
# same editable module; VERSIONS remains frozen-only.
LIVE_VERSION = 'semantic-live'
LIVE_PROMPT_VERSION = _current.PROMPT_VERSION
LIVE_VERSION_NAMES = frozenset({LIVE_VERSION, LIVE_PROMPT_VERSION})
PROMPT_MODULES[LIVE_VERSION] = _current
PROMPT_MODULES[LIVE_PROMPT_VERSION] = _current
# The stable alias stays last for existing CLI defaults and integrations.
SELECTABLE_VERSIONS = VERSIONS + (_live16_snapshot.PROMPT_VERSION,
                                  _live17_snapshot.PROMPT_VERSION,
                                  _live18_snapshot.PROMPT_VERSION,
                                  _live19_snapshot.PROMPT_VERSION,
                                  _live20_snapshot.PROMPT_VERSION,
                                  _live22_snapshot.PROMPT_VERSION,
                                  _live23_snapshot.PROMPT_VERSION,
                                  _live24_snapshot.PROMPT_VERSION,
                                  _live25_snapshot.PROMPT_VERSION,
                                  _live26_snapshot.PROMPT_VERSION,
                                  LIVE_PROMPT_VERSION, LIVE_VERSION)

# Single source of truth for "which version should people actually run".
# Every frozen version stays listed in ``VERSIONS``; these two labels only
# drive the unified entry point (``main.py versions`` / ``main.py status``)
# and the docs, so the recommendation cannot drift between README,
# STRUCTURE and HANDOFF.
RECOMMENDED_VERSION = 'semantic-v3.16'
EXPERIMENTAL_VERSION = 'semantic-v3.20'

# The default is the single editable live prompt; the frozen archive is only
# for replaying historical runs.  Feature parity with v3.16/v3.20 was verified
# at creation time, so switching the default changes only the prompt text.
DEFAULT_VERSION = LIVE_VERSION

VERSIONS_DIR = Path(__file__).resolve().parent / 'versions'


def _from(first):
    """Return the frozen version suffix beginning at ``first``."""
    return frozenset(VERSIONS[VERSIONS.index(first):])


# Centralized feature matrix.  Adding a prompt version should normally require
# one registry edit rather than repeated tuples throughout the pipeline.
STRICT_PIV_VERSIONS = _from('semantic-v3.5')
PLAN_VERSIONS = _from('semantic-v3.5')
STRUCTURED_UNRESOLVED_VERSIONS = _from('semantic-v3.7')
NUMERIC_GUARD_VERSIONS = _from('semantic-v3.10')
ADDRESS_GUARD_VERSIONS = _from('semantic-v3.11')
LEAN_FORMAL_INPUT_VERSIONS = _from('semantic-v3.12')
STEP_NORMALIZATION_VERSIONS = _from('semantic-v3.13')
CORE_COUNT_VERSIONS = _from('semantic-v3.13')
ID_NORMALIZATION_VERSIONS = _from('semantic-v3.14')
RELATION_ALIGNMENT_VERSIONS = _from('semantic-v3.15')
LOCAL_REPAIR_VERSIONS = _from('semantic-v3.16')

REFERENCED_CATALOG_VERSIONS = _from('semantic-v3.5')
ALLOWED_STATEMENT_ID_VERSIONS = _from('semantic-v3.5')
PROTOCOL_IDENTIFIER_EXCLUSION_VERSIONS = frozenset({'semantic-v3.17'})

# Feature lookup decoupled from version names: the live prompt toggles its
# features in ``current.FEATURES`` while frozen versions keep their historical
# sets, so editing the live file can never silently rewrite history.
FEATURE_NAMES = (
    'strict_piv',
    'plan_synthesis',
    'structured_unresolved',
    'numeric_guard',
    'address_guard',
    'lean_formal_input',
    'step_normalization',
    'core_count',
    'id_normalization',
    'relation_alignment',
    'local_repair',
    'referenced_catalog',
    'allowed_statement_ids',
    'protocol_identifier_exclusion',
    'assumption_numeric_relief',
    'symbolic_numeric_relief',
    'duplicate_predicate_gate',
    'requirement_source_review',
    'intent_scope_review',
    'partial_formalization',
    'example_pinning_review',
    'placeholder_predicate_review',
    'semantic_faithfulness_audit',
    'mixed_unit_scaling_review',
    'symbol_table_review',
    'impact_level_claims',
    'impact_section_scope',
    'impact_inventory_stage',
    'frozen_piv_sources',
    'multi_i_claims',
    'unit_guard',
    'fidelity_only_rules',
    'relation_context_generation',
    'relationship_trace',
    'direct_v_prescreen',
    'gate_direct_v_denominator',
    'direct_witness_effects',
)
_LEGACY_FEATURE_SETS = {
    'strict_piv': STRICT_PIV_VERSIONS,
    'plan_synthesis': PLAN_VERSIONS,
    'structured_unresolved': STRUCTURED_UNRESOLVED_VERSIONS,
    'numeric_guard': NUMERIC_GUARD_VERSIONS,
    'address_guard': ADDRESS_GUARD_VERSIONS,
    'lean_formal_input': LEAN_FORMAL_INPUT_VERSIONS,
    'step_normalization': STEP_NORMALIZATION_VERSIONS,
    'core_count': CORE_COUNT_VERSIONS,
    'id_normalization': ID_NORMALIZATION_VERSIONS,
    'relation_alignment': RELATION_ALIGNMENT_VERSIONS,
    'local_repair': LOCAL_REPAIR_VERSIONS,
    'referenced_catalog': REFERENCED_CATALOG_VERSIONS,
    'allowed_statement_ids': ALLOWED_STATEMENT_ID_VERSIONS,
    'protocol_identifier_exclusion': PROTOCOL_IDENTIFIER_EXCLUSION_VERSIONS,
    # No frozen version ships the assumption relief: old runs replay with the
    # strict numeric gate they were produced under.
    'assumption_numeric_relief': frozenset(),
    # Symbolic/illustrative numeric abstraction relief: frozen v3.16 is the
    # recommended line and the gate over-strictness it fixes was reproduced on
    # v3.16 reruns, so the fix ships from v3.16 onward.
    'symbolic_numeric_relief': _from('semantic-v3.16'),
    # Post-closure structural additions (semantic-live-5, 2026-10-08): the same
    # replay rule applies -- no frozen version enables them, so every recorded
    # run keeps the behaviour it was produced under.
    'duplicate_predicate_gate': frozenset(),
    'requirement_source_review': frozenset(),
    'intent_scope_review': frozenset(),
    'partial_formalization': frozenset(),
    # live-6 (2026-10-08): post-holdout defect-side improvements.  Same replay
    # rule: no frozen version enables them, recorded runs keep their own
    # behaviour.
    'example_pinning_review': frozenset(),
    # S15 (2026-10-14, blind-batch_03): same replay rule -- no frozen version
    # enables it, so recorded runs keep the behaviour they were produced under.
    'placeholder_predicate_review': frozenset(),
    # S17 (2026-10-14, blind-batch_06): semantic cross-audit model call; no
    # frozen version enables it, so recorded runs keep the deterministic-only
    # acceptance they were produced under.
    'semantic_faithfulness_audit': frozenset(),
    # S18 (2026-10-14, blind-batch_06/05): two zero-model-call advisories
    # (mixed-unit scaling shape, symbol-table hygiene).  Same replay rule --
    # no frozen version enables them, recorded runs keep their own behaviour.
    'mixed_unit_scaling_review': frozenset(),
    'symbol_table_review': frozenset(),
    # semantic-live-8: inventory report effects and formalize each impact in an
    # independently replayable claim. Frozen prompts keep their prior contract.
    'impact_level_claims': frozenset(),
    # semantic-live-11: deterministic source boundary for extracted impacts.
    # Frozen versions retain their historical unrestricted statement evidence.
    'impact_section_scope': frozenset(),
    # semantic-live-12: extract the Impact inventory from a restricted catalog,
    # then merge it with the separately generated core elements. Frozen versions
    # retain their original single-pass extraction.
    'impact_inventory_stage': frozenset(),
    # semantic-live-16: applicability-selected P/I sources are immutable input
    # to rule generation. Historical prompts keep their recorded behavior.
    'frozen_piv_sources': frozenset(),
    'multi_i_claims': frozenset(),
    # Unit compatibility was historically enforced by the formula compiler.
    # Keep it enabled for archived versions; semantic-live-18 delegates it to
    # the post-generation P/I/V fidelity audit.
    'unit_guard': frozenset(VERSIONS),
    'fidelity_only_rules': frozenset(),
    # semantic-live-23: pass cited action/root-cause excerpts to rule generation
    # while preserving frozen prompt replay behavior for all earlier versions.
    'relation_context_generation': frozenset(),
    'relationship_trace': frozenset(),
    # Applicability direct-V pre-screen is a live-prompt-only denominator
    # refinement; frozen versions keep their historical applicability schema.
    'direct_v_prescreen': frozenset(),
    'gate_direct_v_denominator': frozenset(),
    'direct_witness_effects': frozenset(),
}


def feature_enabled(version, feature):
    """Report whether ``version`` enables the named pipeline feature."""
    if feature not in FEATURE_NAMES:
        raise ValueError(f'unknown prompt feature: {feature}')
    if version not in PROMPT_MODULES:
        raise ValueError(f'unknown prompt version: {version}')
    if version in LIVE_VERSION_NAMES:
        if feature in _current.FEATURES:
            return bool(_current.FEATURES[feature])
        return feature == 'unit_guard'
    module = PROMPT_MODULES[version]
    if hasattr(module, 'FEATURES'):
        if feature in module.FEATURES:
            return bool(module.FEATURES[feature])
        return feature == 'unit_guard'
    return version in _LEGACY_FEATURE_SETS[feature]


def features_for(version):
    """Return the full feature mapping for ``version`` (recorded in provenance)."""
    return {name: feature_enabled(version, name) for name in FEATURE_NAMES}


def module_for(version):
    """Return the frozen prompt module for a public version identifier."""
    try:
        return PROMPT_MODULES[version]
    except KeyError as exc:
        raise ValueError(f'unknown prompt version: {version}') from exc


def source_path_for_legacy_name(name):
    """Resolve a frozen manifest's historical prompt filename after migration."""
    if name not in {f'{module_name}.py' for module_name in MODULE_NAMES}:
        raise ValueError(f'unknown frozen prompt filename: {name}')
    return VERSIONS_DIR / name
