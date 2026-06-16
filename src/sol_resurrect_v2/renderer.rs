use std::collections::{HashMap, HashSet};

use anyhow::{bail, Result};

use super::fallback::FallbackLevel;
use super::slice_atom::SliceAtom;
use super::slice_graph::SliceGraph;
use super::source_db::{is_container_kind, DefId, DefinitionKind, FunctionId, SourceDatabase, StatementId};

pub struct SourceBackedRenderer<'a> {
    source_db: &'a SourceDatabase,
}

impl<'a> SourceBackedRenderer<'a> {
    pub fn new(source_db: &'a SourceDatabase) -> Self {
        Self { source_db }
    }

    pub fn render(&self, graph: &SliceGraph) -> Result<String> {
        if graph.fallback_level() == FallbackLevel::FullSourceUnit {
            return Ok(self.source_db.full_source_text());
        }

        let mut chunks = Vec::new();
        let mut seen = HashSet::new();

        for header in self.source_db.header_texts() {
            push_unique(&mut chunks, &mut seen, header);
        }

        self.render_top_level_types(graph, &mut chunks, &mut seen);
        self.render_containers(graph, &mut chunks, &mut seen)?;

        if chunks
            .iter()
            .all(|chunk| !chunk.contains("contract ") && !chunk.contains("interface "))
        {
            if let Some(target) = self.source_db.resolve_container(&graph.target_contract) {
                self.push_def_text(target, &mut chunks, &mut seen)?;
            } else {
                bail!(
                    "target contract {} not found in SourceDatabase",
                    graph.target_contract
                );
            }
        }

        let output = chunks.join("\n\n");
        self.assert_no_partial_tokens(&output)?;
        Ok(output)
    }

    fn render_top_level_types(
        &self,
        graph: &SliceGraph,
        chunks: &mut Vec<String>,
        seen: &mut HashSet<String>,
    ) {
        for atom in &graph.atoms {
            match atom {
                SliceAtom::TypeDefinition(def_id)
                | SliceAtom::UsingDirective(def_id)
                | SliceAtom::ContainerItem(def_id) => {
                    if let Some(def) = self.source_db.def_index.defs.get(def_id) {
                        if def.container.is_none() && !is_container_kind(def_id.kind) {
                            let _ = self.push_def_text(*def_id, chunks, seen);
                        }
                    }
                }
                _ => {}
            }
        }
    }

    fn render_containers(
        &self,
        graph: &SliceGraph,
        chunks: &mut Vec<String>,
        seen: &mut HashSet<String>,
    ) -> Result<()> {
        let mut full_containers = Vec::<DefId>::new();
        let mut selected_containers = Vec::<DefId>::new();
        let mut member_texts: HashMap<DefId, Vec<String>> = HashMap::new();
        let mut statement_functions: HashMap<FunctionId, Vec<StatementId>> = HashMap::new();
        let mut whole_functions = HashSet::<FunctionId>::new();

        for atom in &graph.atoms {
            if let SliceAtom::Function(function_id)
            | SliceAtom::LibraryMember(function_id)
            | SliceAtom::StatementWindow { function: function_id } = atom
            {
                whole_functions.insert(*function_id);
            }
        }

        for atom in &graph.atoms {
            match atom {
                SliceAtom::FullContainer(def_id) => full_containers.push(*def_id),
                SliceAtom::Function(function_id) | SliceAtom::LibraryMember(function_id) => {
                    let def_id = function_id.def_id;
                    if let Some(def) = self.source_db.def_index.defs.get(&def_id) {
                        if let Some(container) = &def.container {
                            if let Some(container_id) = self.source_db.resolve_container(container)
                            {
                                selected_containers.push(container_id);
                                if let Some(text) = self.source_db.get_function_text(*function_id) {
                                    member_texts
                                        .entry(container_id)
                                        .or_default()
                                        .push(indent_member(text));
                                }
                            }
                        }
                    }
                }
                SliceAtom::Statement(statement_id) => {
                    let function_id = statement_id.enclosing_function;
                    if whole_functions.contains(&function_id) {
                        continue;
                    }
                    if let Some(function) = self.source_db.function_index.functions.get(&function_id) {
                        if let Some(container) = &function.container {
                            if let Some(container_id) = self.source_db.resolve_container(container) {
                                selected_containers.push(container_id);
                                statement_functions
                                    .entry(function_id)
                                    .or_default()
                                    .push(*statement_id);
                            }
                        }
                    }
                }
                SliceAtom::StatementWindow { function } => {
                    if let Some(function_def) = self.source_db.function_index.functions.get(function) {
                        if let Some(container) = &function_def.container {
                            if let Some(container_id) = self.source_db.resolve_container(container) {
                                selected_containers.push(container_id);
                                let ids = self
                                    .source_db
                                    .function_statements(*function)
                                    .into_iter()
                                    .map(|(statement_id, _)| statement_id)
                                    .collect::<Vec<_>>();
                                statement_functions.entry(*function).or_default().extend(ids);
                            }
                        }
                    }
                }
                SliceAtom::ContainerItem(def_id) => {
                    if let Some(def) = self.source_db.def_index.defs.get(def_id) {
                        if is_container_kind(def_id.kind) {
                            selected_containers.push(*def_id);
                        } else if let Some(container) = &def.container {
                            if let Some(container_id) = self.source_db.resolve_container(container)
                            {
                                selected_containers.push(container_id);
                                if let Some(text) = self.source_db.get_source_text(*def_id) {
                                    member_texts
                                        .entry(container_id)
                                        .or_default()
                                        .push(indent_member(text));
                                }
                            }
                        }
                    }
                }
                SliceAtom::TypeDefinition(def_id) | SliceAtom::UsingDirective(def_id) => {
                    if let Some(def) = self.source_db.def_index.defs.get(def_id) {
                        if let Some(container) = &def.container {
                            if let Some(container_id) = self.source_db.resolve_container(container) {
                                selected_containers.push(container_id);
                                if let Some(text) = self.source_db.get_source_text(*def_id) {
                                    member_texts
                                        .entry(container_id)
                                        .or_default()
                                        .push(indent_member(text));
                                }
                            }
                        }
                    }
                }
                _ => {}
            }
        }

        for (function_id, mut statement_ids) in statement_functions {
            statement_ids.sort_by_key(|id| id.node_id);
            statement_ids.dedup();
            if let Some(function) = self.source_db.function_index.functions.get(&function_id) {
                if let Some(container) = &function.container {
                    if let Some(container_id) = self.source_db.resolve_container(container) {
                        let text = self.render_statement_function(function_id, &statement_ids)?;
                        member_texts.entry(container_id).or_default().push(text);
                    }
                }
            }
        }

        full_containers.sort_by_key(|id| container_bucket(id.kind));
        full_containers.dedup();
        let full_set = full_containers.iter().copied().collect::<HashSet<_>>();

        selected_containers.sort_by_key(|id| {
            (
                container_bucket(id.kind),
                self.source_db
                    .def_index
                    .defs
                    .get(id)
                    .map(|def| def.span.start)
                    .unwrap_or(usize::MAX),
                !member_texts.contains_key(id),
            )
        });
        selected_containers.dedup();

        for def_id in full_containers {
            self.push_def_text(def_id, chunks, seen)?;
        }
        let mut rendered_container_names = HashSet::new();
        for def_id in selected_containers {
            if full_set.contains(&def_id) {
                continue;
            }
            if let Some(def) = self.source_db.def_index.defs.get(&def_id) {
                if !rendered_container_names.insert(def.name.clone()) {
                    continue;
                }
            }
            let text = self.render_container_shell(def_id, member_texts.remove(&def_id).unwrap_or_default())?;
            push_unique(chunks, seen, text);
        }

        Ok(())
    }

    fn render_container_shell(&self, def_id: DefId, members: Vec<String>) -> Result<String> {
        let Some(signature) = self.source_db.get_signature_text(def_id) else {
            bail!("missing container signature for {:?}", def_id);
        };
        let mut header = signature.trim().to_string();
        if !header.ends_with('{') {
            header.push_str(" {");
        }
        let mut unique = HashSet::new();
        let mut output = Vec::new();
        output.push(header);
        for member in members {
            let normalized = member.trim().to_string();
            if !normalized.is_empty() && unique.insert(normalized.clone()) {
                output.push(normalized);
            }
        }
        output.push("}".to_string());
        Ok(output.join("\n"))
    }

    fn render_statement_function(
        &self,
        function_id: FunctionId,
        statements: &[StatementId],
    ) -> Result<String> {
        let Some(signature) = self.source_db.get_signature_text(function_id.def_id) else {
            bail!("missing function signature for {:?}", function_id);
        };
        let mut header = signature.trim().to_string();
        if header.ends_with('{') {
            header.pop();
            header = header.trim_end().to_string();
        }
        if header.ends_with(';') {
            return Ok(indent_member(&header));
        }
        let mut lines = Vec::new();
        lines.push(format!("    {} {{", header.trim()));
        for statement_id in statements {
            if let Some(statement) = self.source_db.get_statement_text(*statement_id) {
                lines.push(indent_statement(statement));
            }
        }
        lines.push("    }".to_string());
        Ok(lines.join("\n"))
    }

    fn push_def_text(
        &self,
        def_id: DefId,
        chunks: &mut Vec<String>,
        seen: &mut HashSet<String>,
    ) -> Result<()> {
        let Some(text) = self.source_db.get_source_text(def_id) else {
            bail!("missing source text for {:?}", def_id);
        };
        push_unique(chunks, seen, text.trim().to_string());
        Ok(())
    }

    fn assert_no_partial_tokens(&self, output: &str) -> Result<()> {
        let trimmed = output.trim();
        if matches!(trimmed, ");" | ",);" | "return (" | "SomeStruct({") {
            bail!(
                "renderer invariant violation: renderer attempted to emit a partial Solidity atom: {}",
                trimmed
            );
        }
        Ok(())
    }
}

fn push_unique(chunks: &mut Vec<String>, seen: &mut HashSet<String>, text: String) {
    let normalized = text.trim().to_string();
    if !normalized.is_empty() && seen.insert(normalized.clone()) {
        chunks.push(normalized);
    }
}

fn indent_member(text: &str) -> String {
    text.trim()
        .lines()
        .map(|line| {
            if line.trim().is_empty() {
                String::new()
            } else {
                format!("    {}", line.trim_end())
            }
        })
        .collect::<Vec<_>>()
        .join("\n")
}

fn indent_statement(text: &str) -> String {
    text.trim()
        .lines()
        .map(|line| {
            if line.trim().is_empty() {
                String::new()
            } else {
                format!("        {}", line.trim_end())
            }
        })
        .collect::<Vec<_>>()
        .join("\n")
}

fn container_bucket(kind: DefinitionKind) -> usize {
    match kind {
        DefinitionKind::Interface => 3,
        DefinitionKind::Library => 4,
        DefinitionKind::AbstractContract => 6,
        DefinitionKind::Contract => 8,
        _ => 9,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::sol_resurrect_v2::frontend::SourceFrontend;
    use crate::sol_resurrect_v2::slice_graph::SliceGraph;

    #[test]
    fn renderer_rejects_partial_statement_token() {
        let db = SourceDatabase::default();
        let renderer = SourceBackedRenderer::new(&db);
        assert!(renderer.assert_no_partial_tokens(");").is_err());
        assert!(renderer
            .assert_no_partial_tokens("function f() external {\n    g(\n        1\n    );\n}")
            .is_ok());
    }
}
