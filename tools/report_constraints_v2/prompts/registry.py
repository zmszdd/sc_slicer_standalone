"""Single registry for prompt versions and their supported pipeline features.

Keep version-specific prompt text in ``prompts/versions``.  Runtime code should
depend on this registry instead of importing every historical module itself.
"""

from importlib import import_module
from pathlib import Path

# Importing the package installs the frozen-version directory on sys.path.  The
# source files can therefore keep their historical absolute import statements.
from . import versions as _versions  # noqa: F401


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
)

MODULES = tuple(import_module(f'{__package__}.versions.{name}')
                for name in MODULE_NAMES)
PROMPT_MODULES = {module.PROMPT_VERSION: module for module in MODULES}
VERSIONS = tuple(PROMPT_MODULES)

# Single source of truth for "which version should people actually run".
# Every frozen version stays listed in ``VERSIONS``; these two labels only
# drive the unified entry point (``main.py versions`` / ``main.py status``)
# and the docs, so the recommendation cannot drift between README,
# STRUCTURE and HANDOFF.
RECOMMENDED_VERSION = 'semantic-v3.16'
EXPERIMENTAL_VERSION = 'semantic-v3.19'

# The default is the recommended version; the historical pre-v3.5 versions
# were removed on 2026-09-22.
DEFAULT_VERSION = RECOMMENDED_VERSION

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
