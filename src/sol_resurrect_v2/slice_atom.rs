use serde::Serialize;

use super::source_db::{DefId, FunctionId, SourceId, StatementId};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize)]
pub enum SliceAtom {
    Statement(StatementId),
    StatementWindow { function: FunctionId },
    Function(FunctionId),
    LibraryMember(FunctionId),
    ContainerItem(DefId),
    TypeDefinition(DefId),
    UsingDirective(DefId),
    InheritanceEdge { child: DefId, parent: DefId },
    FullContainer(DefId),
    FullSourceUnit(SourceId),
}

impl SliceAtom {
    pub fn is_source_backed(self) -> bool {
        true
    }
}
