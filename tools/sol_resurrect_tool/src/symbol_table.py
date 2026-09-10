from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Dict, List, Optional, Set


@dataclass
class SymbolRecord:
    name: str
    kind: str
    owner: str = "global"
    scope: str = "global"
    source: str = "original"
    line: Optional[int] = None
    text: Optional[str] = None


@dataclass
class SymbolTable:
    records: List[SymbolRecord] = field(default_factory=list)
    by_name: Dict[str, List[SymbolRecord]] = field(default_factory=dict)

    def add(self, record: SymbolRecord) -> None:
        self.records.append(record)
        self.by_name.setdefault(record.name, []).append(record)

    def is_defined(self, name: str, owner: Optional[str] = None, scope: Optional[str] = None) -> bool:
        return any(
            r.name == name
            and (owner is None or r.owner == owner)
            and (scope is None or r.scope == scope)
            for r in self.records
        )

    def defined_kinds(self, name: str, owner: Optional[str] = None, scope: Optional[str] = None) -> Set[str]:
        return {
            r.kind
            for r in self.records
            if r.name == name and (owner is None or r.owner == owner) and (scope is None or r.scope == scope)
        }

    def has_cross_kind_conflict(self, name: str, owner: Optional[str] = None, scope: Optional[str] = None) -> bool:
        kinds = self.defined_kinds(name, owner=owner, scope=scope)
        return len(kinds) > 1

    def duplicate_definitions(self) -> Dict[str, List[SymbolRecord]]:
        return {name: records for name, records in self.by_name.items() if len(records) > 1}

    def all_names(self) -> Set[str]:
        return set(self.by_name.keys())


def build_symbol_table(code: str) -> SymbolTable:
    table = SymbolTable()
    patterns = [
        (r"\bcontract\s+([A-Za-z_][A-Za-z0-9_]*)", "contract"),
        (r"\binterface\s+([A-Za-z_][A-Za-z0-9_]*)", "interface"),
        (r"\blibrary\s+([A-Za-z_][A-Za-z0-9_]*)", "library"),
        (r"\bstruct\s+([A-Za-z_][A-Za-z0-9_]*)", "struct"),
        (r"\benum\s+([A-Za-z_][A-Za-z0-9_]*)", "enum"),
        (r"\berror\s+([A-Za-z_][A-Za-z0-9_]*)", "error"),
        (r"\btype\s+([A-Za-z_][A-Za-z0-9_]*)\s+is\b", "type"),
        (r"\bfunction\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", "function"),
    ]
    for pattern, kind in patterns:
        for m in re.finditer(pattern, code):
            table.add(SymbolRecord(name=m.group(1), kind=kind, line=None, text=m.group(0)))
    return table
