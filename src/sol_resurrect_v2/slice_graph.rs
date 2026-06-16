use std::collections::HashSet;

use super::fallback::FallbackLevel;
use super::slice_atom::SliceAtom;
use super::source_db::{DefId, FunctionId, StatementId};

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum SliceNode {
    Function(FunctionId),
    StateVar(DefId),
    Type(DefId),
    LibraryMember(FunctionId),
    UsingDirective(DefId),
    Event(DefId),
    Error(DefId),
    Modifier(DefId),
    Contract(DefId),
    Interface(DefId),
    Library(DefId),
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum SliceEdge {
    DataDependency,
    ControlDependency,
    LocalDefinition,
    FunctionCall,
    TypeReference,
    MemberReference,
    UsingExtension,
    Inheritance,
    ConstructorDependency,
    TestHarnessDependency,
    ExternalBoundary,
}

#[derive(Debug, Clone)]
pub struct SliceGraph {
    pub target_contract: String,
    pub target_function: String,
    pub focus_symbol: String,
    pub nodes: HashSet<SliceNode>,
    pub atoms: HashSet<SliceAtom>,
    fallback_level: FallbackLevel,
}

impl SliceGraph {
    pub fn seed(target_contract: String, target_function: String, focus_symbol: String) -> Self {
        Self {
            target_contract,
            target_function,
            focus_symbol,
            nodes: HashSet::new(),
            atoms: HashSet::new(),
            fallback_level: FallbackLevel::MinimalStatementSlice,
        }
    }

    pub fn add_atom(&mut self, atom: SliceAtom) -> bool {
        self.atoms.insert(atom)
    }

    pub fn add_container(&mut self, def_id: DefId) -> bool {
        self.add_atom(SliceAtom::FullContainer(def_id))
    }

    pub fn add_function(&mut self, function_id: FunctionId) -> bool {
        self.nodes.insert(SliceNode::Function(function_id));
        self.add_atom(SliceAtom::Function(function_id))
    }

    pub fn add_statement(&mut self, statement_id: StatementId) -> bool {
        self.add_atom(SliceAtom::Statement(statement_id))
    }

    pub fn set_fallback_level(&mut self, level: FallbackLevel) {
        self.fallback_level = level;
    }

    pub fn fallback_level(&self) -> FallbackLevel {
        self.fallback_level
    }

    pub fn atom_count(&self) -> usize {
        self.atoms.len()
    }

    pub fn target_function_full_restored(&self) -> bool {
        self.atoms
            .iter()
            .any(|atom| matches!(atom, SliceAtom::Function(_)))
            || self.container_fallback_used()
    }

    pub fn container_fallback_used(&self) -> bool {
        self.atoms
            .iter()
            .any(|atom| matches!(atom, SliceAtom::FullContainer(_)))
    }
}
