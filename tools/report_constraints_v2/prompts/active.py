"""Explicit resolver for the prompts actually used by the stage-2 pipeline.

Frozen modules preserve historical experiments.  Runtime code comes through this
facade so callers can inspect one resolved element prompt and one resolved formal
prompt without following the historical inheritance chain.
"""

from dataclasses import dataclass
import hashlib

from .definitions import ELEMENT_CONTRACT_MARKERS, FORMAL_CONTRACT_MARKERS
from .registry import (DEFAULT_VERSION, EXPERIMENTAL_VERSION, LIVE_VERSION,
                       RECOMMENDED_VERSION, module_for)


@dataclass(frozen=True)
class ResolvedPromptSet:
    version: str
    evidence_mode: str
    scope: str
    element_prompt: str
    formal_prompt: str

    def text(self, part: str) -> str:
        if part == 'element':
            return self.element_prompt
        if part == 'formal':
            return self.formal_prompt
        raise ValueError(f'unknown prompt part: {part}')

    def sha256(self, part: str) -> str:
        return hashlib.sha256(self.text(part).encode()).hexdigest()


def _assert_piv_contract(prompts: ResolvedPromptSet) -> None:
    """Fail early if an active prompt loses the canonical P/I/V distinctions."""
    if prompts.version not in {RECOMMENDED_VERSION, EXPERIMENTAL_VERSION, LIVE_VERSION}:
        return
    missing = [marker for marker in ELEMENT_CONTRACT_MARKERS
               if marker not in prompts.element_prompt]
    missing.extend(marker for marker in FORMAL_CONTRACT_MARKERS
                   if marker not in prompts.formal_prompt)
    if missing:
        raise ValueError(
            f'active prompt {prompts.version} violates the canonical P/I/V contract: '
            + '; '.join(missing)
        )


def resolve_prompt_set(version: str = DEFAULT_VERSION, evidence_mode: str = 'ids',
                       scope: str = 'core') -> ResolvedPromptSet:
    """Resolve the exact two prompt strings used for one pipeline run."""
    module = module_for(version)
    element = module.ID_ELEMENT_PROMPT if evidence_mode == 'ids' else module.ELEMENT_PROMPT
    resolved = ResolvedPromptSet(
        version=version,
        evidence_mode=evidence_mode,
        scope=scope,
        element_prompt=element,
        formal_prompt=module.formal_prompt(evidence_mode, scope),
    )
    _assert_piv_contract(resolved)
    return resolved
