"""Versioned and resolved prompt access for the stage-2 pipeline."""

from .active import ResolvedPromptSet, resolve_prompt_set
from .definitions import PIV_DEFINITIONS, render_definitions
from .registry import DEFAULT_VERSION, PROMPT_MODULES, module_for

__all__ = (
    'DEFAULT_VERSION', 'PROMPT_MODULES', 'PIV_DEFINITIONS', 'ResolvedPromptSet',
    'module_for', 'render_definitions', 'resolve_prompt_set',
)
