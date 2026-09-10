from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import List, Optional


@dataclass
class Diagnostic:
    code: str
    kind: str
    message: str
    primary_symbol: Optional[str] = None
    primary_kind: Optional[str] = None
    primary_line: Optional[int] = None
    previous_symbol: Optional[str] = None
    previous_kind: Optional[str] = None
    previous_line: Optional[int] = None


_DUPLICATE_PATTERNS = [
    r"Identifier already declared\.",
    r"Identifier already exists\.",
    r"duplicate",
]

_UNDEFINED_PATTERNS = [
    r"Identifier not found or not unique\.",
    r"Undeclared identifier",
]

_SIGNATURE_PATTERNS = [
    r"wrong argument count",
    r"member .* not found",
    r"invalid implicit conversion",
    r"not implicitly convertible",
]

_SOLIDITY_KEYWORDS = {
    "return", "returns", "if", "else", "for", "while", "do", "break", "continue",
    "require", "revert", "emit", "new", "delete", "function", "contract",
    "interface", "library", "struct", "enum", "error", "event", "modifier",
    "mapping", "address", "bool", "string", "bytes", "uint", "int", "memory",
    "storage", "calldata", "public", "private", "internal", "external", "view",
    "pure", "payable", "unchecked", "assembly",
}


def parse_compiler_diagnostics(compiler_output: str) -> List[Diagnostic]:
    text = compiler_output or ""
    diagnostics: List[Diagnostic] = []
    lines = text.splitlines()

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        kind = None
        code = ""
        if any(re.search(p, stripped, re.I) for p in _DUPLICATE_PATTERNS):
            kind = "duplicate-declaration"
            code = "2333" if "2333" in stripped else "duplicate"
        elif any(re.search(p, stripped, re.I) for p in _UNDEFINED_PATTERNS):
            kind = "undefined-type"
            code = "7920" if "7920" in stripped else "undefined"
        elif any(re.search(p, stripped, re.I) for p in _SIGNATURE_PATTERNS):
            kind = "signature-mismatch"
            code = "signature"
        elif re.search(r"parsererror|declaration expected|expected pragma", stripped, re.I):
            kind = "structure"
            code = "parser"
        else:
            continue

        symbol = None
        m = re.search(r"function\s+([A-Za-z_][A-Za-z0-9_]*)", stripped)
        if m:
            symbol = m.group(1)
        else:
            snippet = ""
            caret_line = ""
            for lookahead in lines[idx + 1: idx + 8]:
                sm = re.match(r"\s*\|\s*(.+)$", lookahead)
                numbered = re.match(r"\s*\d+\s*\|\s*(.+)$", lookahead)
                if numbered:
                    snippet = numbered.group(1)
                elif sm:
                    if "^" in sm.group(1):
                        caret_line = sm.group(1)
                        break
                    else:
                        snippet = sm.group(1)
            m = None
            if snippet and caret_line:
                start_col = caret_line.find('^')
                end_col = caret_line.rfind('^') + 1
                if 0 <= start_col < len(snippet):
                    exact_symbol = snippet[start_col:end_col].strip()
                    if exact_symbol and re.match(r'^_?[A-Za-z][A-Za-z0-9_]*$', exact_symbol):
                        m = re.match(r".*", exact_symbol)
            if not m:
                for candidate in re.findall(r"\b(?!(?:Error|Identifier)\b)(_?[A-Za-z][A-Za-z0-9_]*)\b", snippet):
                    if candidate not in _SOLIDITY_KEYWORDS:
                        m = re.match(r".*", candidate)
                        break
            if not m:
                for candidate in re.findall(r"\b(?!(?:Error|Identifier)\b)(_?[A-Za-z][A-Za-z0-9_]*)\b", stripped):
                    if candidate not in _SOLIDITY_KEYWORDS:
                        m = re.match(r".*", candidate)
                        break
            if m:
                symbol = m.group(0)

        diagnostics.append(
            Diagnostic(
                code=code,
                kind=kind,
                message=stripped,
                primary_symbol=symbol,
                primary_line=idx + 1,
            )
        )
    return diagnostics
