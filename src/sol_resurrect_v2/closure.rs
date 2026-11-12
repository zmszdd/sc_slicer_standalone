use super::feedback::FeedbackAction;
use super::fallback::FallbackLevel;
use super::slice_atom::SliceAtom;
use super::slice_graph::SliceGraph;
use super::source_db::{DefinitionKind, FunctionId, SourceDatabase, StatementId};

pub struct ClosureEngine<'a> {
    source_db: &'a SourceDatabase,
}

impl<'a> ClosureEngine<'a> {
    pub fn new(source_db: &'a SourceDatabase) -> Self {
        Self { source_db }
    }

    pub fn apply_initial_closure(&mut self, graph: &mut SliceGraph) {
        if let Some(target_container) = self.source_db.resolve_container(&graph.target_contract) {
            graph.add_atom(SliceAtom::ContainerItem(target_container));
            self.add_container_scaffold(graph, target_container);
            self.add_inheritance(graph, target_container);
        }
        if let Some(target_fn) = self
            .source_db
            .resolve_function(&graph.target_contract, &graph.target_function)
        {
            let target_statements = self.target_statement_closure(target_fn, &graph.focus_symbol);
            for statement_id in &target_statements {
                graph.add_statement(*statement_id);
            }
            self.add_calls_from_statements(graph, &target_statements);
            if let Some(setup) = self.source_db.resolve_function(&graph.target_contract, "setUp") {
                self.add_function_with_context(graph, setup);
            }
        }
        for def_id in self.source_db.providers_for_symbol(&graph.focus_symbol) {
            graph.add_atom(SliceAtom::ContainerItem(def_id));
        }
    }

    pub fn apply_fallback_level(&mut self, graph: &mut SliceGraph, level: FallbackLevel) -> bool {
        let mut changed = false;
        let Some(target_fn) = self
            .source_db
            .resolve_function(&graph.target_contract, &graph.target_function)
        else {
            return false;
        };
        match level {
            FallbackLevel::TargetStatementWindow => {
                for statement_id in self.target_statement_closure(target_fn, &graph.focus_symbol) {
                    changed |= graph.add_statement(statement_id);
                }
            }
            FallbackLevel::FullHarnessHelpers => {
                for helper in ["setUp", "_setupDefaultOracles", "_setupDefaultMocks"] {
                    if let Some(fid) = self.source_db.resolve_function(&graph.target_contract, helper) {
                        changed |= self.add_function_with_context(graph, fid);
                    }
                }
            }
            FallbackLevel::FullDependencyFunctions
            | FallbackLevel::FullRequiredLibrariesInterfaces => {
                if let Some(function) = self.source_db.function_index.functions.get(&target_fn) {
                    for call in &function.calls {
                        changed |= self.add_helper_group_or_function(graph, call);
                    }
                }
            }
            FallbackLevel::FullTargetTestFunction => {
                changed |= self.add_function_with_context(graph, target_fn);
            }
            _ => {}
        }
        changed
    }

    pub fn apply_feedback(&mut self, graph: &mut SliceGraph, action: &FeedbackAction) -> bool {
        match action {
            FeedbackAction::AddSymbol(symbol) => {
                let mut changed = false;
                for def_id in self.source_db.providers_for_symbol(symbol) {
                    changed |= self.add_def_for_feedback(graph, def_id);
                }
                changed || self.add_helper_group_or_function(graph, symbol)
            }
            FeedbackAction::AddMember {
                receiver_type,
                member,
            } => self.add_member_for_feedback(graph, receiver_type.as_deref(), member),
            FeedbackAction::WidenSyntax | FeedbackAction::WidenContainer | FeedbackAction::Noop => {
                false
            }
        }
    }

    fn add_member_for_feedback(
        &self,
        graph: &mut SliceGraph,
        receiver_type: Option<&str>,
        member: &str,
    ) -> bool {
        if let Some(receiver_type) = receiver_type {
            let fids = self
                .source_db
                .resolve_functions_in_container(receiver_type, member);
            if !fids.is_empty() {
                let mut changed = false;
                for fid in fids {
                    changed |= self.add_function_with_context(graph, fid);
                }
                return changed;
            }
            if let Some(def_ids) = self.source_db.def_index.members_by_container.get(receiver_type) {
                let mut changed = false;
                for def_id in def_ids {
                    let Some(def) = self.source_db.def_index.defs.get(def_id) else {
                        continue;
                    };
                    if def.name == member {
                        changed |= self.add_def_for_feedback(graph, *def_id);
                    }
                }
                if changed {
                    return true;
                }
            }
            if let Some(container_id) = self.source_db.resolve_container(receiver_type) {
                let changed = self.add_base_members_named(graph, container_id, member);
                if changed {
                    return true;
                }
            }
        }
        self.add_helper_group_or_function(graph, member)
    }

    fn add_def_for_feedback(
        &self,
        graph: &mut SliceGraph,
        def_id: super::source_db::DefId,
    ) -> bool {
        let Some(def) = self.source_db.def_index.defs.get(&def_id) else {
            return false;
        };
        match def_id.kind {
            DefinitionKind::Contract
            | DefinitionKind::AbstractContract
            | DefinitionKind::Interface
            | DefinitionKind::Library => {
                let mut changed = graph.add_atom(SliceAtom::ContainerItem(def_id));
                changed |= self.add_container_scaffold(graph, def_id);
                changed |= self.add_inheritance(graph, def_id);
                changed
            }
            DefinitionKind::Function => {
                if let Some(container) = &def.container {
                    if let Some(fid) = self.source_db.resolve_function(container, &def.name) {
                        return self.add_function_with_context(graph, fid);
                    }
                }
                graph.add_atom(SliceAtom::ContainerItem(def_id))
            }
            DefinitionKind::UsingDirective => graph.add_atom(SliceAtom::UsingDirective(def_id)),
            DefinitionKind::Struct
            | DefinitionKind::Enum
            | DefinitionKind::Error
            | DefinitionKind::Event
            | DefinitionKind::UserDefinedValueType => {
                let mut changed = graph.add_atom(SliceAtom::TypeDefinition(def_id));
                if def_id.kind == DefinitionKind::UserDefinedValueType {
                    changed |= self.add_using_directives_for_type(graph, &def.name);
                }
                changed
            }
            _ => graph.add_atom(SliceAtom::ContainerItem(def_id)),
        }
    }

    fn add_using_directives_for_type(&self, graph: &mut SliceGraph, type_name: &str) -> bool {
        let mut changed = false;
        for using_id in &self.source_db.using_index.using_defs {
            let Some(text) = self.source_db.get_source_text(*using_id) else {
                continue;
            };
            if !text.contains(&format!(" for {type_name}")) {
                continue;
            }
            changed |= graph.add_atom(SliceAtom::UsingDirective(*using_id));
            let using_text = text.trim();
            if using_text.strip_prefix("using ").is_some_and(|rest| rest.trim_start().starts_with('{')) {
                for function_name in using_function_names(using_text) {
                    for provider in self.source_db.providers_for_symbol(&function_name) {
                        changed |= self.add_def_for_feedback(graph, provider);
                    }
                }
            } else if let Some(library_name) = using_library_name(text) {
                for provider in self.source_db.providers_for_symbol(&library_name) {
                    changed |= graph.add_atom(SliceAtom::ContainerItem(provider));
                    changed |= self.add_container_scaffold(graph, provider);
                    changed |= self.add_inheritance(graph, provider);
                }
            }
        }
        changed
    }

    fn add_helper_group_or_function(&self, graph: &mut SliceGraph, name: &str) -> bool {
        let mut changed = false;
        if let Some(prefix) = helper_group_prefix(name) {
            for (fid, function) in &self.source_db.function_index.functions {
                if function.name.starts_with(prefix)
                    && function.container.as_deref() == Some(&graph.target_contract)
                {
                    changed |= self.add_function_with_context(graph, *fid);
                }
            }
        }
        if let Some(fid) = self
            .source_db
            .resolve_function(&graph.target_contract, name)
            .or_else(|| {
                self.source_db
                    .function_index
                    .by_name
                    .get(name)
                    .and_then(|ids| ids.first().copied())
            })
        {
            changed |= self.add_function_with_context(graph, fid);
        }
        changed
    }

    fn add_function_with_context(&self, graph: &mut SliceGraph, fid: FunctionId) -> bool {
        if let Some(function) = self.source_db.function_index.functions.get(&fid) {
            if function.container.as_deref() == Some(&graph.target_contract)
                && function.name == graph.target_function
                && graph.fallback_level() < FallbackLevel::FullTargetTestFunction
            {
                let target_statements = self.target_statement_closure(fid, &graph.focus_symbol);
                let mut changed = false;
                for statement_id in &target_statements {
                    changed |= graph.add_statement(*statement_id);
                }
                self.add_calls_from_statements(graph, &target_statements);
                return changed;
            }
        }
        let mut changed = graph.add_function(fid);
        if !changed {
            return false;
        }
        if let Some(function) = self.source_db.function_index.functions.get(&fid) {
            if let Some(container) = &function.container {
                if let Some(container_id) = self.source_db.resolve_container(container) {
                    changed |= graph.add_atom(SliceAtom::ContainerItem(container_id));
                    changed |= self.add_container_scaffold(graph, container_id);
                    changed |= self.add_inheritance(graph, container_id);
                    changed |= self.add_base_members_named(graph, container_id, &function.name);
                    for call in &function.calls {
                        for called in self.source_db.resolve_functions_in_container(container, call) {
                            if called != fid {
                                changed |= self.add_function_with_context(graph, called);
                            }
                        }
                    }
                }
            }
        }
        changed
    }

    fn add_base_members_named(
        &self,
        graph: &mut SliceGraph,
        child: super::source_db::DefId,
        member: &str,
    ) -> bool {
        let mut changed = false;
        let Some(bases) = self.source_db.inheritance_index.bases_by_child.get(&child) else {
            return false;
        };
        for base in bases {
            let Some(base_id) = self.source_db.resolve_container(base) else {
                continue;
            };
            for fid in self.source_db.resolve_functions_in_container(base, member) {
                changed |= self.add_function_with_context(graph, fid);
            }
            if let Some(def_ids) = self.source_db.def_index.members_by_container.get(base) {
                for def_id in def_ids {
                    let Some(def) = self.source_db.def_index.defs.get(def_id) else {
                        continue;
                    };
                    if def.name == member {
                        changed |= self.add_def_for_feedback(graph, *def_id);
                    }
                }
            }
            changed |= self.add_base_members_named(graph, base_id, member);
        }
        changed
    }

    fn add_inheritance(&self, graph: &mut SliceGraph, child: super::source_db::DefId) -> bool {
        let mut changed = false;
        let Some(bases) = self.source_db.inheritance_index.bases_by_child.get(&child) else {
            return false;
        };
        for base in bases {
            if let Some(base_id) = self.source_db.resolve_container(base) {
                changed |= graph.add_atom(SliceAtom::ContainerItem(base_id));
                changed |= self.add_container_scaffold(graph, base_id);
                changed |= self.add_child_implementations_for_base(graph, child, base);
                changed |= self.add_inheritance(graph, base_id);
            }
        }
        changed
    }

    fn add_child_implementations_for_base(
        &self,
        graph: &mut SliceGraph,
        child: super::source_db::DefId,
        base: &str,
    ) -> bool {
        let mut changed = false;
        let Some(child_def) = self.source_db.def_index.defs.get(&child) else {
            return false;
        };
        let Some(base_members) = self.source_db.def_index.members_by_container.get(base) else {
            return false;
        };
        for base_member_id in base_members {
            if base_member_id.kind != DefinitionKind::Function {
                continue;
            }
            let Some(base_member) = self.source_db.def_index.defs.get(base_member_id) else {
                continue;
            };
            for fid in self
                .source_db
                .resolve_functions_in_container(&child_def.name, &base_member.name)
            {
                changed |= self.add_function_with_context(graph, fid);
            }
        }
        changed
    }

    fn add_container_scaffold(
        &self,
        graph: &mut SliceGraph,
        container_id: super::source_db::DefId,
    ) -> bool {
        let mut changed = false;
        let Some(container) = self.source_db.def_index.defs.get(&container_id) else {
            return false;
        };
        let Some(member_ids) = self.source_db.def_index.members_by_container.get(&container.name) else {
            return false;
        };
        for member_id in member_ids {
            match member_id.kind {
                DefinitionKind::StateVariable
                | DefinitionKind::Constant
                | DefinitionKind::Modifier
                | DefinitionKind::Struct
                | DefinitionKind::Enum
                | DefinitionKind::Error
                | DefinitionKind::Event
                | DefinitionKind::UserDefinedValueType => {
                    changed |= graph.add_atom(SliceAtom::ContainerItem(*member_id));
                }
                DefinitionKind::UsingDirective => {
                    changed |= graph.add_atom(SliceAtom::ContainerItem(*member_id));
                    if let Some(text) = self.source_db.get_source_text(*member_id) {
                        if let Some(library_name) = using_library_name(text) {
                            for provider in self.source_db.providers_for_symbol(&library_name) {
                                changed |= graph.add_atom(SliceAtom::ContainerItem(provider));
                                changed |= self.add_container_scaffold(graph, provider);
                                changed |= self.add_inheritance(graph, provider);
                            }
                        }
                    }
                }
                DefinitionKind::Function => {
                    if let Some(member) = self.source_db.def_index.defs.get(member_id) {
                        if member.name == "constructor" || is_mock_container(&container.name) {
                            for fid in self
                                .source_db
                                .resolve_functions_in_container(&container.name, &member.name)
                            {
                                changed |= self.add_function_with_context(graph, fid);
                            }
                        }
                    }
                }
                _ => {}
            }
        }
        changed
    }

    fn target_statement_closure(
        &self,
        function_id: FunctionId,
        focus_symbol: &str,
    ) -> Vec<StatementId> {
        let statements = self.source_db.function_statements(function_id);
        let mut selected = Vec::<StatementId>::new();
        let mut selected_names = std::collections::HashSet::<String>::new();

        for (statement_id, text) in &statements {
            if text.contains(focus_symbol) {
                selected.push(*statement_id);
                for name in identifiers(text) {
                    selected_names.insert(name);
                }
            }
        }

        let mut changed = true;
        while changed {
            changed = false;
            for (statement_id, text) in statements.iter().rev() {
                if selected.contains(statement_id) {
                    continue;
                }
                if defines_any(text, &selected_names)
                    || (uses_any(text, &selected_names) && has_side_effect(text))
                {
                    selected.push(*statement_id);
                    for name in identifiers(text) {
                        selected_names.insert(name);
                    }
                    changed = true;
                }
            }
        }

        selected.sort_by_key(|id| id.node_id);
        selected.dedup();
        selected
    }

    fn add_calls_from_statements(&self, graph: &mut SliceGraph, statement_ids: &[StatementId]) {
        for statement_id in statement_ids {
            let Some(text) = self.source_db.get_statement_text(*statement_id) else {
                continue;
            };
            for call in call_names(text) {
                self.add_helper_group_or_function(graph, &call);
            }
        }
    }
}

fn is_mock_container(name: &str) -> bool {
    name.starts_with("Mock") || name.ends_with("Mock")
}

fn using_function_names(text: &str) -> Vec<String> {
    let Some(inner) = text
        .split_once('{')
        .and_then(|(_, rest)| rest.split_once('}').map(|(inner, _)| inner))
    else {
        return Vec::new();
    };
    inner
        .split(',')
        .filter_map(|part| read_using_function_name(part.trim()))
        .collect()
}

fn read_using_function_name(part: &str) -> Option<String> {
    let name = part.split_whitespace().next()?;
    let clean = name.trim_matches(|ch: char| !ch.is_ascii_alphanumeric() && ch != '_');
    (!clean.is_empty()).then(|| clean.to_string())
}

fn helper_group_prefix(name: &str) -> Option<&'static str> {
    if name.starts_with("_getArg") {
        return Some("_getArg");
    }
    if name.starts_with("_getImmutable") {
        return Some("_getImmutable");
    }
    if name.starts_with("_getPool") {
        return Some("_getPool");
    }
    None
}

fn defines_any(text: &str, names: &std::collections::HashSet<String>) -> bool {
    names.iter().any(|name| {
        let escaped = regex::escape(name);
        let assign = regex::Regex::new(&format!(r"\b{}\b\s*(?:=|\[)", escaped)).unwrap();
        let declaration = regex::Regex::new(&format!(
            r"\b(?:[A-Za-z_][A-Za-z0-9_\.]*(?:\[[^\]]*\])*\s+)+(?:memory\s+|storage\s+|calldata\s+)?{}\b",
            escaped
        ))
        .unwrap();
        assign.is_match(text) || declaration.is_match(text)
    })
}

fn uses_any(text: &str, names: &std::collections::HashSet<String>) -> bool {
    names.iter().any(|name| {
        let escaped = regex::escape(name);
        regex::Regex::new(&format!(r"\b{}\b", escaped))
            .unwrap()
            .is_match(text)
    })
}

fn has_side_effect(text: &str) -> bool {
    let trimmed = text.trim_start();
    trimmed.contains('(')
        && (trimmed.contains('.')
            || trimmed.contains(" = ")
            || trimmed.contains("+=")
            || trimmed.contains("-=")
            || trimmed.contains("++")
            || trimmed.contains("--"))
}

fn identifiers(text: &str) -> Vec<String> {
    text.split(|ch: char| !(ch.is_ascii_alphanumeric() || ch == '_'))
        .filter(|part| !part.is_empty())
        .filter(|part| !SOLIDITY_WORDS.contains(part))
        .filter(|part| part.chars().next().is_some_and(|ch| ch.is_ascii_alphabetic() || ch == '_'))
        .map(|part| part.to_string())
        .collect()
}

fn call_names(text: &str) -> Vec<String> {
    let mut calls = Vec::new();
    let bytes = text.as_bytes();
    let mut idx = 0usize;
    while idx < bytes.len() {
        if bytes[idx].is_ascii_alphabetic() || bytes[idx] == b'_' {
            let start = idx;
            idx += 1;
            while idx < bytes.len() && (bytes[idx].is_ascii_alphanumeric() || bytes[idx] == b'_') {
                idx += 1;
            }
            let ident = &text[start..idx];
            let mut look = idx;
            while look < bytes.len() && bytes[look].is_ascii_whitespace() {
                look += 1;
            }
            if look < bytes.len() && bytes[look] == b'(' && !SOLIDITY_WORDS.contains(&ident) {
                calls.push(ident.to_string());
            }
        } else {
            idx += 1;
        }
    }
    calls
}

fn using_library_name(text: &str) -> Option<String> {
    let rest = text.trim().strip_prefix("using ")?;
    let rest = rest.trim_start();
    if rest.starts_with('{') {
        let after_brace = rest.split_once('}')?.1.trim_start();
        return after_brace
            .strip_prefix("for ")
            .and_then(|part| identifiers(part).into_iter().next());
    }
    rest.split_whitespace()
        .next()
        .map(|name| name.trim_end_matches(';').to_string())
        .filter(|name| !name.is_empty())
}

const SOLIDITY_WORDS: &[&str] = &[
    "if", "for", "while", "return", "require", "assert", "revert", "emit", "new", "delete",
    "mapping", "function", "modifier", "event", "error", "memory", "storage", "calldata",
    "public", "private", "internal", "external", "view", "pure", "payable", "returns",
    "uint", "uint256", "uint128", "uint64", "uint32", "uint24", "uint16", "uint8",
    "int", "int256", "int128", "int64", "int32", "int24", "int16", "int8", "address",
    "bool", "bytes", "bytes32", "string", "true", "false",
];
