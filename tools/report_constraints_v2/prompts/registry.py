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
# ``VERSIONS`` stays frozen-only: the live prompt is appended to
# ``PROMPT_MODULES`` afterwards so it never leaks into the ``_from()`` slices.
VERSIONS = tuple(PROMPT_MODULES)

LIVE_VERSION = _current.PROMPT_VERSION
PROMPT_MODULES[LIVE_VERSION] = _current
# Versions selectable on the command line: the frozen archive plus the live
# file that is maintained in place.
SELECTABLE_VERSIONS = VERSIONS + (LIVE_VERSION,)

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
    'duplicate_predicate_gate',
    'requirement_source_review',
    'intent_scope_review',
    'partial_formalization',
    'example_pinning_review',
    'placeholder_predicate_review',
    'semantic_faithfulness_audit',
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
}


def feature_enabled(version, feature):
    """Report whether ``version`` enables the named pipeline feature."""
    if feature not in FEATURE_NAMES:
        raise ValueError(f'unknown prompt feature: {feature}')
    if version not in PROMPT_MODULES:
        raise ValueError(f'unknown prompt version: {version}')
    if version == LIVE_VERSION:
        return bool(_current.FEATURES.get(feature))
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
