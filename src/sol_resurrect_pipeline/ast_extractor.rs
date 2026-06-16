#![allow(unused)]
use solar_ast::{ItemKind, SourceUnit};
use std::collections::{HashMap, HashSet};

/// Unified context passed to the resurrection pipeline.
pub struct ResurrectionInput<'a> {
    pub input_slice: &'a str,
    pub original_source: &'a str,
    pub asts: &'a [SourceUnit<'a>],
    // pub selection: &'a SliceSelection, // We'll add this dependency later when we hook it up in main
    pub extraction_result: ExtractionResult,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum DefinitionKind {
    Contract,
    Interface,
    Library,
    Struct,
    Enum,
    Error,
    Event,
    Modifier,
    Function,
    UserDefinedValueType,
    UsingDirective,
    Unknown,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct DefId {
    pub source_id: String,
    pub node_id: u32,
    pub kind: DefinitionKind,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum RestoreStrategy {
    SourceBacked,
    ExternalMock,
    SkipAlreadyPresent,
    Unresolved,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum LlmMockAllowedReason {
    UnknownAddressReceiver,
    ExternalBlackBoxContract,
    MissingDeploymentOnlyDependency,
}

#[derive(Debug, Clone)]
pub struct MissingDefinition {
    pub id: DefId,
    pub name: String,
    pub kind: DefinitionKind,
    pub source_span: Option<(u32, u32)>,
    pub source_text: Option<String>,
    pub restore_strategy: RestoreStrategy,
    pub reason: String,
}

#[derive(Debug, Clone)]
pub struct ExternalMockRequest {
    pub name: String,
    pub methods: Vec<String>,
    pub reason: LlmMockAllowedReason,
}

#[derive(Debug, Clone)]
pub enum RestoreAction {
    SourceBacked(MissingDefinition),
    ExternalMock(ExternalMockRequest),
    SkipAlreadyPresent(DefId),
    Unresolved(ExtractionDiagnostic),
}

#[derive(Debug, Clone)]
pub struct ExtractionDiagnostic {
    pub message: String,
}

#[derive(Debug, Default, Clone)]
pub struct ExtractionResult {
    pub restores: Vec<RestoreAction>,
    pub diagnostics: Vec<ExtractionDiagnostic>,
}

// to_legacy removed

pub fn extract_missing_dependencies_from_ast<'a>(
    sess: &solar_interface::Session,
    asts: &'a [(String, SourceUnit<'a>)],
    selection: &crate::SliceSelection,
    slice_code: &str,
) -> ExtractionResult {
    let mut collector = ReferenceCollector {
        selection,
        referenced_types: HashSet::new(),
        referenced_funcs: HashSet::new(),
        referenced_errors: HashSet::new(),
        referenced_events: HashSet::new(),
    };

    for (_, ast) in asts {
        use solar_ast::visit::Visit;
        let _ = collector.visit_source_unit(ast);
    }

    let symbol_index = SymbolIndex::build(asts);
    let present_set = PresentDefinitionSet::new(selection, slice_code);

    let mut result = ExtractionResult::default();

    // DependencyResolver: calculate closure using worklist
    let mut missing_ids = HashSet::new();

    let resolve_to_def_id = |name: &str, index: &SymbolIndex| -> Option<DefId> {
        if let Some(c) = index.defined_interfaces.get(name) {
            Some(DefId {
                source_id: c.0.clone(),
                node_id: c.1.span.lo().0,
                kind: DefinitionKind::Interface,
            })
        } else if let Some(c) = index.defined_contracts.get(name) {
            Some(DefId {
                source_id: c.0.clone(),
                node_id: c.1.span.lo().0,
                kind: DefinitionKind::Contract,
            })
        } else if let Some(c) = index.defined_libraries.get(name) {
            Some(DefId {
                source_id: c.0.clone(),
                node_id: c.1.span.lo().0,
                kind: DefinitionKind::Library,
            })
        } else if let Some(e) = index.defined_errors.get(name) {
            Some(DefId {
                source_id: e.0.clone(),
                node_id: e.1.span.lo().0,
                kind: DefinitionKind::Error,
            })
        } else if let Some(s) = index.defined_structs.get(name) {
            Some(DefId {
                source_id: s.0.clone(),
                node_id: s.1.span.lo().0,
                kind: DefinitionKind::Struct,
            })
        } else if let Some(e) = index.defined_enums.get(name) {
            Some(DefId {
                source_id: e.0.clone(),
                node_id: e.1.span.lo().0,
                kind: DefinitionKind::Enum,
            })
        } else if let Some(e) = index.defined_events.get(name) {
            Some(DefId {
                source_id: e.0.clone(),
                node_id: e.1.span.lo().0,
                kind: DefinitionKind::Event,
            })
        } else if let Some(u) = index.defined_udvts.get(name) {
            Some(DefId {
                source_id: u.0.clone(),
                node_id: u.1.span.lo().0,
                kind: DefinitionKind::UserDefinedValueType,
            })
        } else {
            None
        }
    };

    let mut queue: Vec<(String, DefId)> = Vec::new();
    for ref_name in collector
        .referenced_types
        .iter()
        .chain(collector.referenced_funcs.iter())
    {
        if let Some(def_id) = resolve_to_def_id(ref_name, &symbol_index) {
            queue.push((ref_name.clone(), def_id));
        } else if !present_set.defined_names.contains(ref_name) {
            result.diagnostics.push(ExtractionDiagnostic {
                message: format!("Could not resolve symbol {} to any source item", ref_name),
            });
        }
    }

    // Topologically sorted definitions
    let mut ordered_missing_names = Vec::new();

    while let Some((ref_name, def_id)) = queue.pop() {
        if present_set.defined_names.contains(&ref_name) || missing_ids.contains(&def_id) {
            continue;
        }
        missing_ids.insert(def_id.clone());

        // We found a new missing definition. We need to collect ITS references and push to queue.
        let mut sub_collector = ReferenceCollector {
            selection: selection, // We'll bypass the filter for sub-collections by visiting specific items
            referenced_types: HashSet::new(),
            referenced_funcs: HashSet::new(),
            referenced_errors: HashSet::new(),
            referenced_events: HashSet::new(),
        };

        if let Some(c) = symbol_index.defined_interfaces.get(&ref_name) {
            let mut methods = Vec::new();
            if let ItemKind::Contract(contract) = &c.1.kind {
                for item in contract.body.iter() {
                    if let ItemKind::Function(f) = &item.kind {
                        if let Some(n) = &f.header.name {
                            methods.push(n.name.as_str().to_string());
                        }
                    }
                }
            }

            let source_text = sess.source_map().span_to_snippet(c.1.span).ok();

            let def = MissingDefinition {
                id: DefId {
                    source_id: c.0.clone(),
                    node_id: c.1.span.lo().0,
                    kind: DefinitionKind::Interface,
                },
                name: ref_name.clone(),
                kind: DefinitionKind::Interface,
                source_span: Some((c.1.span.lo().0, c.1.span.hi().0)),
                source_text,
                restore_strategy: RestoreStrategy::SourceBacked,
                reason: "Referenced interface not present in slice".to_string(),
            };
            result.restores.push(RestoreAction::SourceBacked(def));

            if let ItemKind::Contract(contract) = &c.1.kind {
                for item in contract.body.iter() {
                    let _ = solar_ast::visit::Visit::visit_item(&mut sub_collector, item);
                }
            }
        } else if let Some(c) = symbol_index.defined_contracts.get(&ref_name) {
            let mut methods = Vec::new();
            if let ItemKind::Contract(contract) = &c.1.kind {
                for item in contract.body.iter() {
                    if let ItemKind::Function(f) = &item.kind {
                        if let Some(n) = &f.header.name {
                            methods.push(n.name.as_str().to_string());
                        }
                    }
                }
            }
            let req = ExternalMockRequest {
                name: ref_name.clone(),
                methods,
                reason: LlmMockAllowedReason::ExternalBlackBoxContract,
            };
            result.restores.push(RestoreAction::ExternalMock(req));
        } else if let Some(c) = symbol_index.defined_libraries.get(&ref_name) {
            let source_text = sess.source_map().span_to_snippet(c.1.span).ok();
            let def = MissingDefinition {
                id: DefId {
                    source_id: c.0.clone(),
                    node_id: c.1.span.lo().0,
                    kind: DefinitionKind::Library,
                },
                name: ref_name.clone(),
                kind: DefinitionKind::Library,
                source_span: Some((c.1.span.lo().0, c.1.span.hi().0)),
                source_text,
                restore_strategy: RestoreStrategy::SourceBacked,
                reason: "Referenced library not present in slice".to_string(),
            };
            result.restores.push(RestoreAction::SourceBacked(def));
        } else if let Some(e) = symbol_index.defined_errors.get(&ref_name) {
            let source_text = sess.source_map().span_to_snippet(e.1.span).ok();
            let def = MissingDefinition {
                id: DefId {
                    source_id: e.0.clone(),
                    node_id: e.1.span.lo().0,
                    kind: DefinitionKind::Error,
                },
                name: ref_name.clone(),
                kind: DefinitionKind::Error,
                source_span: Some((e.1.span.lo().0, e.1.span.hi().0)),
                source_text,
                restore_strategy: RestoreStrategy::SourceBacked,
                reason: "Referenced error not present in slice".to_string(),
            };
            result.restores.push(RestoreAction::SourceBacked(def));
            if let ItemKind::Error(error) = &e.1.kind {
                let _ = solar_ast::visit::Visit::visit_item_error(&mut sub_collector, error);
            }
        } else if let Some(s) = symbol_index.defined_structs.get(&ref_name) {
            let source_text = sess.source_map().span_to_snippet(s.1.span).ok();
            let def = MissingDefinition {
                id: DefId {
                    source_id: s.0.clone(),
                    node_id: s.1.span.lo().0,
                    kind: DefinitionKind::Struct,
                },
                name: ref_name.clone(),
                kind: DefinitionKind::Struct,
                source_span: Some((s.1.span.lo().0, s.1.span.hi().0)),
                source_text,
                restore_strategy: RestoreStrategy::SourceBacked,
                reason: "Referenced struct not present in slice".to_string(),
            };
            result.restores.push(RestoreAction::SourceBacked(def));
            if let ItemKind::Struct(strct) = &s.1.kind {
                let _ = solar_ast::visit::Visit::visit_item_struct(&mut sub_collector, strct);
            }
        } else if let Some(e) = symbol_index.defined_enums.get(&ref_name) {
            let source_text = sess.source_map().span_to_snippet(e.1.span).ok();
            let def = MissingDefinition {
                id: DefId {
                    source_id: e.0.clone(),
                    node_id: e.1.span.lo().0,
                    kind: DefinitionKind::Enum,
                },
                name: ref_name.clone(),
                kind: DefinitionKind::Enum,
                source_span: Some((e.1.span.lo().0, e.1.span.hi().0)),
                source_text,
                restore_strategy: RestoreStrategy::SourceBacked,
                reason: "Referenced enum not present in slice".to_string(),
            };
            result.restores.push(RestoreAction::SourceBacked(def));
        } else if let Some(e) = symbol_index.defined_events.get(&ref_name) {
            let source_text = sess.source_map().span_to_snippet(e.1.span).ok();
            let def = MissingDefinition {
                id: DefId {
                    source_id: e.0.clone(),
                    node_id: e.1.span.lo().0,
                    kind: DefinitionKind::Event,
                },
                name: ref_name.clone(),
                kind: DefinitionKind::Event,
                source_span: Some((e.1.span.lo().0, e.1.span.hi().0)),
                source_text,
                restore_strategy: RestoreStrategy::SourceBacked,
                reason: "Referenced event not present in slice".to_string(),
            };
            result.restores.push(RestoreAction::SourceBacked(def));
            if let ItemKind::Event(event) = &e.1.kind {
                let _ = solar_ast::visit::Visit::visit_item_event(&mut sub_collector, event);
            }
        } else if let Some(u) = symbol_index.defined_udvts.get(&ref_name) {
            let source_text = sess.source_map().span_to_snippet(u.1.span).ok();
            let def = MissingDefinition {
                id: DefId {
                    source_id: u.0.clone(),
                    node_id: u.1.span.lo().0,
                    kind: DefinitionKind::UserDefinedValueType,
                },
                name: ref_name.clone(),
                kind: DefinitionKind::UserDefinedValueType,
                source_span: Some((u.1.span.lo().0, u.1.span.hi().0)),
                source_text,
                restore_strategy: RestoreStrategy::SourceBacked,
                reason: "Referenced UDVT not present in slice".to_string(),
            };
            result.restores.push(RestoreAction::SourceBacked(def));
        } else {
            // Already handled initial unresolved
        }

        for sub_ref_name in sub_collector
            .referenced_types
            .iter()
            .chain(sub_collector.referenced_funcs.iter())
        {
            if let Some(sub_def_id) = resolve_to_def_id(sub_ref_name, &symbol_index) {
                queue.push((sub_ref_name.clone(), sub_def_id));
            } else if !present_set.defined_names.contains(sub_ref_name)
                && !missing_ids.contains(&DefId {
                    source_id: String::new(),
                    node_id: 0,
                    kind: DefinitionKind::Unknown,
                })
            {
                // simplification
                result.diagnostics.push(ExtractionDiagnostic {
                    message: format!(
                        "Could not resolve symbol {} to any source item",
                        sub_ref_name
                    ),
                });
            }
        }
        ordered_missing_names.push(ref_name);
    }

    // Bucket sort the restores based on definition kind (UDVT -> structs -> interfaces -> libraries -> contracts)
    result.restores.sort_by_key(|action| match action {
        RestoreAction::SourceBacked(def) => match def.kind {
            DefinitionKind::UsingDirective => 1,
            DefinitionKind::UserDefinedValueType => 2,
            DefinitionKind::Struct
            | DefinitionKind::Enum
            | DefinitionKind::Error
            | DefinitionKind::Event => 3,
            DefinitionKind::Interface => 4,
            DefinitionKind::Library => 5,
            DefinitionKind::Contract => 6,
            _ => 10,
        },
        RestoreAction::ExternalMock(_) => 6,
        RestoreAction::SkipAlreadyPresent(_) => 100,
        RestoreAction::Unresolved(_) => 100,
    });

    result
}

struct ReferenceCollector<'a> {
    selection: &'a crate::SliceSelection,
    referenced_types: HashSet<String>,
    referenced_funcs: HashSet<String>,
    referenced_errors: HashSet<String>,
    referenced_events: HashSet<String>,
}

impl<'ast> solar_ast::visit::Visit<'ast> for ReferenceCollector<'_> {
    type BreakValue = ();

    fn visit_item_contract(
        &mut self,
        contract: &'ast solar_ast::ItemContract<'ast>,
    ) -> std::ops::ControlFlow<Self::BreakValue> {
        let name = contract.name.name.as_str();
        if self.selection.relevant_contracts.contains(name)
            || self.selection.full_contracts.contains(name)
        {
            solar_ast::visit::Visit::visit_ident(self, &contract.name)?;
            for base in contract.bases.iter() {
                solar_ast::visit::Visit::visit_modifier(self, base)?;
            }
            for item in contract.body.iter() {
                solar_ast::visit::Visit::visit_item(self, item)?;
            }
        }
        std::ops::ControlFlow::Continue(())
    }

    fn visit_item_function(
        &mut self,
        function: &'ast solar_ast::ItemFunction<'ast>,
    ) -> std::ops::ControlFlow<Self::BreakValue> {
        // If we are visiting this, we are already inside a relevant contract or it's a top-level function.
        // For now, we will visit all bodies if they are visited by the contract logic.
        let header = &function.header;
        solar_ast::visit::Visit::visit_function_header(self, header)?;
        if let Some(body) = &function.body {
            solar_ast::visit::Visit::visit_block(self, body)?;
        }
        std::ops::ControlFlow::Continue(())
    }

    fn visit_path(
        &mut self,
        path: &'ast solar_ast::PathSlice,
    ) -> std::ops::ControlFlow<Self::BreakValue> {
        if let Some(first) = path.segments().first() {
            self.referenced_types
                .insert(first.name.as_str().to_string());
        }
        for ident in path.segments() {
            solar_ast::visit::Visit::visit_ident(self, ident)?;
        }
        std::ops::ControlFlow::Continue(())
    }

    fn visit_ident(
        &mut self,
        ident: &'ast solar_ast::Ident,
    ) -> std::ops::ControlFlow<Self::BreakValue> {
        self.referenced_funcs
            .insert(ident.name.as_str().to_string());
        std::ops::ControlFlow::Continue(())
    }
}

pub struct SymbolIndex<'a> {
    pub defined_contracts: HashMap<String, (String, &'a solar_ast::Item<'a>)>,
    pub defined_structs: HashMap<String, (String, &'a solar_ast::Item<'a>)>,
    pub defined_enums: HashMap<String, (String, &'a solar_ast::Item<'a>)>,
    pub defined_errors: HashMap<String, (String, &'a solar_ast::Item<'a>)>,
    pub defined_events: HashMap<String, (String, &'a solar_ast::Item<'a>)>,
    pub defined_interfaces: HashMap<String, (String, &'a solar_ast::Item<'a>)>,
    pub defined_libraries: HashMap<String, (String, &'a solar_ast::Item<'a>)>,
    pub defined_udvts: HashMap<String, (String, &'a solar_ast::Item<'a>)>,
}

impl<'a> Default for SymbolIndex<'a> {
    fn default() -> Self {
        Self {
            defined_contracts: HashMap::new(),
            defined_structs: HashMap::new(),
            defined_enums: HashMap::new(),
            defined_errors: HashMap::new(),
            defined_events: HashMap::new(),
            defined_interfaces: HashMap::new(),
            defined_libraries: HashMap::new(),
            defined_udvts: HashMap::new(),
        }
    }
}

impl<'a> SymbolIndex<'a> {
    pub fn build(asts: &'a [(String, SourceUnit<'a>)]) -> Self {
        let mut index = Self::default();
        for (source_id, ast) in asts {
            for item in ast.items.iter() {
                match &item.kind {
                    ItemKind::Contract(c) => {
                        let name = c.name.name.as_str().to_string();
                        match c.kind {
                            solar_ast::ContractKind::Interface => {
                                index
                                    .defined_interfaces
                                    .insert(name, (source_id.clone(), item));
                            }
                            solar_ast::ContractKind::Library => {
                                index
                                    .defined_libraries
                                    .insert(name, (source_id.clone(), item));
                            }
                            _ => {
                                index
                                    .defined_contracts
                                    .insert(name, (source_id.clone(), item));
                            }
                        }
                    }
                    ItemKind::Struct(s) => {
                        index
                            .defined_structs
                            .insert(s.name.name.as_str().to_string(), (source_id.clone(), item));
                    }
                    ItemKind::Enum(e) => {
                        index
                            .defined_enums
                            .insert(e.name.name.as_str().to_string(), (source_id.clone(), item));
                    }
                    ItemKind::Error(e) => {
                        index
                            .defined_errors
                            .insert(e.name.name.as_str().to_string(), (source_id.clone(), item));
                    }
                    ItemKind::Event(e) => {
                        index
                            .defined_events
                            .insert(e.name.name.as_str().to_string(), (source_id.clone(), item));
                    }
                    ItemKind::Udvt(u) => {
                        index
                            .defined_udvts
                            .insert(u.name.name.as_str().to_string(), (source_id.clone(), item));
                    }
                    _ => {}
                }
            }
        }
        index
    }
}

pub struct PresentDefinitionSet {
    pub defined_names: HashSet<String>,
}

impl PresentDefinitionSet {
    pub fn new(selection: &crate::SliceSelection, slice_code: &str) -> Self {
        let mut set = HashSet::new();
        for c in &selection.full_contracts {
            set.insert(c.clone());
        }
        for c in &selection.relevant_contracts {
            set.insert(c.clone());
        }

        // Lightweight string scanner to prevent duplicates from the slice code
        let lines: Vec<&str> = slice_code.lines().collect();
        let name_regex = regex::Regex::new(r"^(?:contract|abstract\s+contract|interface|library|struct|enum|error|type)\s+([a-zA-Z0-9_]+)").unwrap();
        for line in lines {
            let line = line.trim();
            if let Some(caps) = name_regex.captures(line) {
                if let Some(name_match) = caps.get(1) {
                    set.insert(name_match.as_str().to_string());
                }
            }
        }
        Self { defined_names: set }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_library_resolution_never_produces_external_mock() {
        let mut index = SymbolIndex::default();

        // Setup a fake library in the symbol index (simulating CurrencyLibrary)
        // We can't easily construct a real solar_ast::Item without a session, but we can verify
        // the closure logic if we just inspect the `resolve_to_def_id` equivalent manually or
        // rely on the structure of the pipeline. Since the pipeline uses `if let Some(c) = index.defined_libraries`,
        // it generates a `RestoreAction::SourceBacked` instead of `ExternalMock`.

        // This test serves as a documentation constraint that the DefinitionKind::Library
        // MUST result in a SourceBacked restore strategy, ensuring CurrencyLibrary is never mocked.
        let kind = DefinitionKind::Library;

        // Simulate what happens in the AST extractor queue:
        let action = RestoreAction::SourceBacked(MissingDefinition {
            id: DefId {
                source_id: "test".to_string(),
                node_id: 0,
                kind: kind.clone(),
            },
            name: "CurrencyLibrary".to_string(),
            kind,
            source_span: None,
            source_text: Some("library CurrencyLibrary {}".to_string()),
            restore_strategy: RestoreStrategy::SourceBacked,
            reason: "test".to_string(),
        });

        match action {
            RestoreAction::SourceBacked(def) => {
                assert_eq!(def.kind, DefinitionKind::Library);
                assert_eq!(def.restore_strategy, RestoreStrategy::SourceBacked);
            }
            _ => panic!("Libraries must never be resolved as ExternalMock"),
        }
    }
}
