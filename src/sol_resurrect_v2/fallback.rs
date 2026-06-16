use serde::Serialize;

use super::slice_atom::SliceAtom;
use super::slice_graph::SliceGraph;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize)]
pub enum FallbackLevel {
    MinimalStatementSlice = 0,
    TargetStatementWindow = 1,
    FullHarnessHelpers = 2,
    FullDependencyFunctions = 3,
    FullRequiredLibrariesInterfaces = 4,
    FullTargetTestFunction = 5,
    FullTargetContractHarness = 6,
    FullSourceUnit = 7,
    OriginalProjectFallback = 8,
}

impl FallbackLevel {
    pub fn as_usize(self) -> usize {
        self as usize
    }

    pub fn name(self) -> &'static str {
        match self {
            Self::MinimalStatementSlice => "minimal_statement_slice",
            Self::TargetStatementWindow => "target_statement_window",
            Self::FullHarnessHelpers => "full_harness_helpers",
            Self::FullDependencyFunctions => "full_dependency_functions",
            Self::FullRequiredLibrariesInterfaces => "full_required_libraries_interfaces",
            Self::FullTargetTestFunction => "full_target_test_function",
            Self::FullTargetContractHarness => "full_target_contract_harness",
            Self::FullSourceUnit => "full_source_unit",
            Self::OriginalProjectFallback => "original_project_fallback",
        }
    }

    pub fn minimality(self) -> &'static str {
        match self {
            Self::MinimalStatementSlice => "source-backed target container seed",
            Self::TargetStatementWindow => "source-backed target statement window",
            Self::FullHarnessHelpers => "target harness plus helpers",
            Self::FullDependencyFunctions => "function-level closure",
            Self::FullRequiredLibrariesInterfaces => "library/interface closure",
            Self::FullTargetTestFunction => "full target function",
            Self::FullTargetContractHarness => "full target contract",
            Self::FullSourceUnit => "full source-backed unit",
            Self::OriginalProjectFallback => "original project classification",
        }
    }

    fn next(self) -> Option<Self> {
        match self {
            Self::MinimalStatementSlice => Some(Self::TargetStatementWindow),
            Self::TargetStatementWindow => Some(Self::FullHarnessHelpers),
            Self::FullHarnessHelpers => Some(Self::FullDependencyFunctions),
            Self::FullDependencyFunctions => Some(Self::FullRequiredLibrariesInterfaces),
            Self::FullRequiredLibrariesInterfaces => Some(Self::FullTargetTestFunction),
            Self::FullTargetTestFunction => Some(Self::FullTargetContractHarness),
            Self::FullTargetContractHarness => Some(Self::FullSourceUnit),
            Self::FullSourceUnit => Some(Self::OriginalProjectFallback),
            Self::OriginalProjectFallback => None,
        }
    }
}

#[derive(Debug, Clone)]
pub struct FallbackController {
    level: FallbackLevel,
    compile_guarantee: bool,
    compile_artifact_fallback: bool,
}

impl FallbackController {
    pub fn new(compile_guarantee: bool) -> Self {
        let compile_artifact_fallback = std::env::var("SC_SLICER_COMPILE_ARTIFACT_FALLBACK")
            .map(|value| value != "0" && !value.trim().is_empty())
            .unwrap_or(false);
        Self {
            level: FallbackLevel::MinimalStatementSlice,
            compile_guarantee,
            compile_artifact_fallback,
        }
    }

    pub fn level(&self) -> FallbackLevel {
        self.level
    }

    pub fn widen(&mut self, graph: &mut SliceGraph) -> bool {
        let Some(next) = self.level.next() else {
            return false;
        };
        let max_effective_level = FallbackLevel::FullRequiredLibrariesInterfaces;
        if next > max_effective_level && !self.compile_artifact_fallback {
            return false;
        }
        if !self.compile_guarantee && next > FallbackLevel::FullDependencyFunctions {
            return false;
        }
        self.level = next;
        graph.set_fallback_level(next);
        if next == FallbackLevel::FullSourceUnit {
            graph.add_atom(SliceAtom::FullSourceUnit(super::source_db::SourceId(0)));
        }
        true
    }
}
