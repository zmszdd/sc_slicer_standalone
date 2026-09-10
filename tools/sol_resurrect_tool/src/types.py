from pydantic import BaseModel, Field
from typing import List, Dict, Set, Optional

class CodeBlock(BaseModel):
    name: str
    code: str
    start_byte: int
    end_byte: int

class ContractShell(CodeBlock):
    state_variables: List[str] = Field(default_factory=list)
    
class OrphanFunction(CodeBlock):
    used_identifiers: List[str] = Field(default_factory=list)
    call_expressions: List[str] = Field(default_factory=list)
    member_accesses: List[str] = Field(default_factory=list)
    return_contexts: List[str] = Field(default_factory=list)

class SymbolIndex(BaseModel):
    contracts: Set[str] = Field(default_factory=set)
    interfaces: Set[str] = Field(default_factory=set)
    libraries: Set[str] = Field(default_factory=set)
    structs: Set[str] = Field(default_factory=set)
    errors: Set[str] = Field(default_factory=set)
    enums: Set[str] = Field(default_factory=set)
    types: Set[str] = Field(default_factory=set)
    functions: Set[str] = Field(default_factory=set)
    state_variables: Set[str] = Field(default_factory=set)
    nested_types: Dict[str, Set[str]] = Field(default_factory=dict)
    nested_errors: Dict[str, Set[str]] = Field(default_factory=dict)
    references: Dict[str, Set[str]] = Field(default_factory=dict)
    conflicts: Dict[str, Set[str]] = Field(default_factory=dict)
    all_identifiers: Set[str] = Field(default_factory=set)
    owners: Dict[str, str] = Field(default_factory=dict)
    scopes: Dict[str, str] = Field(default_factory=dict)
    sources: Dict[str, str] = Field(default_factory=dict)

class RepairAction(BaseModel):
    action: str
    target: str
    details: Dict[str, str] = Field(default_factory=dict)

class RepairPlan(BaseModel):
    category: str
    rationale: str = ""
    actions: List[RepairAction] = Field(default_factory=list)
    reject_reason: Optional[str] = None

class SymbolManifest(BaseModel):
    """AST 解析结果的中间表示"""
    pragmas: List[str] = Field(default_factory=list)
    imports: List[str] = Field(default_factory=list)
    global_types: List[str] = Field(default_factory=list)
    libraries: List[CodeBlock] = Field(default_factory=list)
    contracts: Dict[str, ContractShell] = Field(default_factory=dict)
    orphans: List[OrphanFunction] = Field(default_factory=list)
    symbols: SymbolIndex = Field(default_factory=SymbolIndex)
    
class InferenceResult(BaseModel):
    """LLM 推理结果"""
    rehoming_map: Dict[str, str] = Field(default_factory=dict)
    mock_libraries: Dict[str, str] = Field(default_factory=dict)

class AtomStats(BaseModel):
    statements: int = 0
    functions: int = 0
    libraries: int = 0
    interfaces: int = 0
    contracts: int = 0
    types: int = 0

class GrowBudget(BaseModel):
    max_line_ratio: float = 0.25
    max_byte_ratio: float = 0.30
    max_target_window_ratio: float = 0.40
    max_dependency_functions: int = 200
    max_library_members: int = 300
    max_full_small_libraries: int = 15
    max_full_containers: int = 0

class SliceResult(BaseModel):
    compile_success: bool
    slice_effective: bool

    input_lines: int
    output_lines: int
    line_ratio: float

    input_bytes: int
    output_bytes: int
    byte_ratio: float

    fallback_level: str = "EffectiveSlice"
    target_function_full_restored: bool = False
    target_contract_full_restored: bool = False
    full_source_unit_restored: bool = False

    llm_used: bool = False
    base_container_restore_count: int = 0

    atom_stats: AtomStats = Field(default_factory=AtomStats)
    shrink_removed_atoms: int = 0

    failure_reason: Optional[str] = None
