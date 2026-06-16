use std::collections::{HashMap, HashSet};
use std::path::PathBuf;

use anyhow::{Context, Result};
use serde::Serialize;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize)]
pub struct SourceId(pub usize);

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize)]
pub struct DefId {
    pub source_id: SourceId,
    pub node_id: usize,
    pub kind: DefinitionKind,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize)]
pub struct FunctionId {
    pub def_id: DefId,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize)]
pub struct StatementId {
    pub source_id: SourceId,
    pub node_id: usize,
    pub enclosing_function: FunctionId,
    pub span: SourceSpan,
    pub kind: StatementKind,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize)]
pub struct SourceSpan {
    pub start: usize,
    pub end: usize,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize)]
pub enum DefinitionKind {
    Contract,
    AbstractContract,
    Interface,
    Library,
    Function,
    Modifier,
    StateVariable,
    Constant,
    Struct,
    Enum,
    Error,
    Event,
    UserDefinedValueType,
    UsingDirective,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize)]
pub enum StatementKind {
    VariableDeclaration,
    ExpressionStatement,
    Return,
    If,
    For,
    While,
    Block,
    TryCatch,
    Emit,
    Revert,
    Assembly,
}

#[derive(Debug, Clone)]
pub struct SourceFile {
    pub id: SourceId,
    pub path: PathBuf,
    pub text: String,
}

#[derive(Debug, Clone)]
pub struct Definition {
    pub id: DefId,
    pub name: String,
    pub container: Option<String>,
    pub span: SourceSpan,
    pub signature_span: SourceSpan,
}

#[derive(Debug, Clone)]
pub struct FunctionDefinition {
    pub id: FunctionId,
    pub name: String,
    pub container: Option<String>,
    pub span: SourceSpan,
    pub body_span: Option<SourceSpan>,
    pub calls: HashSet<String>,
}

#[derive(Debug, Clone, Default)]
pub struct DefIndex {
    pub defs: HashMap<DefId, Definition>,
    pub by_name: HashMap<String, Vec<DefId>>,
    pub container_defs: HashMap<String, DefId>,
    pub members_by_container: HashMap<String, Vec<DefId>>,
}

#[derive(Debug, Clone, Default)]
pub struct StatementIndex {
    pub statements: HashMap<StatementId, String>,
}

#[derive(Debug, Clone, Default)]
pub struct FunctionIndex {
    pub functions: HashMap<FunctionId, FunctionDefinition>,
    pub by_name: HashMap<String, Vec<FunctionId>>,
    pub by_container_name: HashMap<(String, String), FunctionId>,
}

#[derive(Debug, Clone, Default)]
pub struct ReferenceIndex {
    pub providers_by_symbol: HashMap<String, HashSet<DefId>>,
}

#[derive(Debug, Clone, Default)]
pub struct TypeIndex {
    pub type_defs: HashSet<DefId>,
}

#[derive(Debug, Clone, Default)]
pub struct UsingIndex {
    pub using_defs: HashSet<DefId>,
}

#[derive(Debug, Clone, Default)]
pub struct InheritanceIndex {
    pub bases_by_child: HashMap<DefId, Vec<String>>,
}

#[derive(Debug, Clone, Default)]
pub struct SourceAst;

#[derive(Debug, Clone, Default)]
pub struct SourceDatabase {
    pub files: Vec<SourceFile>,
    pub ast: SourceAst,
    pub def_index: DefIndex,
    pub stmt_index: StatementIndex,
    pub function_index: FunctionIndex,
    pub ref_index: ReferenceIndex,
    pub type_index: TypeIndex,
    pub using_index: UsingIndex,
    pub inheritance_index: InheritanceIndex,
    pub top_level_headers: Vec<(SourceId, SourceSpan)>,
}

impl SourceDatabase {
    pub fn build(input_files: &[PathBuf]) -> Result<Self> {
        let mut db = SourceDatabase::default();
        for path in input_files {
            let text = std::fs::read_to_string(path)
                .with_context(|| format!("failed to read Solidity source {}", path.display()))?;
            let id = SourceId(db.files.len());
            db.files.push(SourceFile {
                id,
                path: path.clone(),
                text,
            });
        }

        for source_idx in 0..db.files.len() {
            db.index_source_file(SourceId(source_idx));
        }

        Ok(db)
    }

    pub fn log_summary(&self) {
        crate::execution_log::detail(
            "resurrection_v2_source_db",
            format!(
                "files={} defs={} functions={} statements={} types={} using={}",
                self.files.len(),
                self.def_index.defs.len(),
                self.function_index.functions.len(),
                self.stmt_index.statements.len(),
                self.type_index.type_defs.len(),
                self.using_index.using_defs.len()
            ),
        );
    }

    pub fn get_source_text(&self, def_id: DefId) -> Option<&str> {
        let def = self.def_index.defs.get(&def_id)?;
        self.span_text(def_id.source_id, def.span)
    }

    pub fn get_signature_text(&self, def_id: DefId) -> Option<&str> {
        let def = self.def_index.defs.get(&def_id)?;
        self.span_text(def_id.source_id, def.signature_span)
    }

    pub fn get_statement_text(&self, statement_id: StatementId) -> Option<&str> {
        self.span_text(statement_id.source_id, statement_id.span)
    }

    pub fn get_function_text(&self, function_id: FunctionId) -> Option<&str> {
        let function = self.function_index.functions.get(&function_id)?;
        self.span_text(function.id.def_id.source_id, function.span)
    }

    pub fn resolve_container(&self, name: &str) -> Option<DefId> {
        self.def_index.container_defs.get(name).copied()
    }

    pub fn resolve_function(&self, container: &str, name: &str) -> Option<FunctionId> {
        self.function_index
            .by_container_name
            .get(&(container.to_string(), name.to_string()))
            .copied()
            .or_else(|| {
                self.function_index
                    .by_name
                    .get(name)
                    .and_then(|ids| ids.first().copied())
            })
    }

    pub fn resolve_function_in_container(&self, container: &str, name: &str) -> Option<FunctionId> {
        self.function_index
            .by_container_name
            .get(&(container.to_string(), name.to_string()))
            .copied()
    }

    pub fn resolve_functions_in_container(&self, container: &str, name: &str) -> Vec<FunctionId> {
        let mut fids = self
            .function_index
            .functions
            .iter()
            .filter_map(|(fid, function)| {
                (function.container.as_deref() == Some(container) && function.name == name)
                    .then_some(*fid)
            })
            .collect::<Vec<_>>();
        fids.sort_by_key(|fid| (fid.def_id.source_id.0, fid.def_id.node_id));
        fids
    }

    pub fn providers_for_symbol(&self, symbol: &str) -> Vec<DefId> {
        let mut providers = self
            .ref_index
            .providers_by_symbol
            .get(symbol)
            .map(|ids| ids.iter().copied().collect::<Vec<_>>())
            .unwrap_or_default();
        if providers.is_empty() {
            if let Some(def_id) = self.def_index.container_defs.get(symbol) {
                providers.push(*def_id);
            }
        }
        if providers.is_empty() {
            if let Some(def_ids) = self.def_index.by_name.get(symbol) {
                providers.extend(def_ids.iter().copied());
            }
        }
        providers.sort_by_key(|id| (id.source_id.0, id.node_id));
        providers.dedup();
        providers
    }

    pub fn span_text(&self, source_id: SourceId, span: SourceSpan) -> Option<&str> {
        let file = self.files.get(source_id.0)?;
        file.text.get(span.start..span.end)
    }

    pub fn full_source_text(&self) -> String {
        self.files
            .iter()
            .map(|file| file.text.trim_end())
            .collect::<Vec<_>>()
            .join("\n\n")
    }

    pub fn total_nonblank_lines(&self) -> usize {
        self.files
            .iter()
            .map(|file| file.text.lines().filter(|line| !line.trim().is_empty()).count())
            .sum()
    }

    pub fn total_bytes(&self) -> usize {
        self.files.iter().map(|file| file.text.len()).sum()
    }

    pub fn function_statements(&self, function_id: FunctionId) -> Vec<(StatementId, String)> {
        let mut statements = self
            .stmt_index
            .statements
            .iter()
            .filter(|(statement_id, _)| statement_id.enclosing_function == function_id)
            .map(|(statement_id, text)| (*statement_id, text.clone()))
            .collect::<Vec<_>>();
        statements.sort_by_key(|(statement_id, _)| statement_id.node_id);
        statements
    }

    pub fn header_texts(&self) -> Vec<String> {
        let mut seen = HashSet::new();
        let mut headers = Vec::new();
        for (source_id, span) in &self.top_level_headers {
            if let Some(text) = self.span_text(*source_id, *span) {
                let normalized = text.trim().to_string();
                if seen.insert(normalized.clone()) {
                    headers.push(normalized);
                }
            }
        }
        headers
    }

    fn index_source_file(&mut self, source_id: SourceId) {
        let Some(file) = self.files.get(source_id.0) else {
            return;
        };
        let text = file.text.clone();
        let mut offset = 0usize;
        let mut node_id = source_id.0 * 1_000_000;
        while offset < text.len() {
            let Some((line_start, line_end, trimmed)) = next_nonempty_line(&text, offset) else {
                break;
            };
            offset = line_end;

            if trimmed.starts_with("pragma ") || trimmed.starts_with("import ") {
                self.top_level_headers.push((
                    source_id,
                    SourceSpan {
                        start: line_start,
                        end: line_end,
                    },
                ));
                continue;
            }

            if trimmed.starts_with("using ") {
                node_id += 1;
                let span = SourceSpan {
                    start: line_start,
                    end: line_end,
                };
                self.add_definition(
                    DefId {
                        source_id,
                        node_id,
                        kind: DefinitionKind::UsingDirective,
                    },
                    using_name(trimmed).unwrap_or_else(|| format!("using@{}", line_start)),
                    None,
                    span,
                    span,
                );
                continue;
            }

            if let Some((kind, name)) = parse_definition_head(trimmed) {
                let end = if starts_container_or_function(kind) {
                    find_balanced_item_end(&text, line_start).unwrap_or(line_end)
                } else {
                    find_semicolon_end(&text, line_start).unwrap_or(line_end)
                };
                node_id += 1;
                let span = SourceSpan {
                    start: line_start,
                    end,
                };
                let signature_span = SourceSpan {
                    start: line_start,
                    end: find_signature_end(&text, line_start, end),
                };
                let def_id = DefId {
                    source_id,
                    node_id,
                    kind,
                };
                let name = self.name_for_span(kind, source_id, span).unwrap_or(name);
                self.add_definition(def_id, name.clone(), None, span, signature_span);

                if is_container_kind(kind) {
                    self.index_container_members(def_id, &name, span);
                    if let Some(bases) =
                        parse_inheritance(&text[signature_span.start..signature_span.end])
                    {
                        self.inheritance_index.bases_by_child.insert(def_id, bases);
                    }
                }

                offset = end;
            }
        }
    }

    fn index_container_members(
        &mut self,
        container_id: DefId,
        container_name: &str,
        container_span: SourceSpan,
    ) {
        let Some(source) = self.span_text(container_id.source_id, container_span) else {
            return;
        };
        let source = source.to_string();
        let body_start_relative = match source.find('{') {
            Some(idx) => idx + 1,
            None => return,
        };
        let body_end_relative = source.rfind('}').unwrap_or(source.len());
        let mut cursor = body_start_relative;
        let mut node_id = container_id.node_id.saturating_mul(10_000);
        while cursor < body_end_relative {
            let absolute_cursor = container_span.start + cursor;
            let Some((line_start, line_end, trimmed)) = next_nonempty_line(&source, cursor) else {
                break;
            };
            cursor = line_end;
            if line_start >= body_end_relative {
                break;
            }

            if trimmed.starts_with("//") || trimmed.starts_with("/*") {
                continue;
            }

            if trimmed.starts_with("using ") {
                node_id += 1;
                let span = SourceSpan {
                    start: container_span.start + line_start,
                    end: container_span.start + line_end,
                };
                self.add_definition(
                    DefId {
                        source_id: container_id.source_id,
                        node_id,
                        kind: DefinitionKind::UsingDirective,
                    },
                    using_name(trimmed).unwrap_or_else(|| format!("using@{}", span.start)),
                    Some(container_name.to_string()),
                    span,
                    span,
                );
                cursor = line_end;
                continue;
            }

            if let Some((kind, name)) = parse_definition_head(trimmed) {
                let end = if starts_container_or_function(kind) {
                    find_balanced_item_end(&source, line_start).unwrap_or(line_end)
                } else {
                    find_semicolon_end(&source, line_start).unwrap_or(line_end)
                };
                node_id += 1;
                let span = SourceSpan {
                    start: container_span.start + line_start,
                    end: container_span.start + end,
                };
                let signature_span = SourceSpan {
                    start: container_span.start + line_start,
                    end: container_span.start + find_signature_end(&source, line_start, end),
                };
                let def_id = DefId {
                    source_id: container_id.source_id,
                    node_id,
                    kind,
                };
                let name = self
                    .name_for_span(kind, container_id.source_id, span)
                    .unwrap_or(name);
                self.add_definition(
                    def_id,
                    name.clone(),
                    Some(container_name.to_string()),
                    span,
                    signature_span,
                );

                if kind == DefinitionKind::Function {
                    let calls = extract_call_names(
                        self.span_text(container_id.source_id, span)
                            .unwrap_or_default(),
                    );
                    let body_span = find_body_span(
                        self.span_text(container_id.source_id, span)
                            .unwrap_or_default(),
                    )
                    .map(|local| SourceSpan {
                        start: span.start + local.start,
                        end: span.start + local.end,
                    });
                    let fid = FunctionId { def_id };
                    self.function_index.functions.insert(
                        fid,
                        FunctionDefinition {
                            id: fid,
                            name: name.clone(),
                            container: Some(container_name.to_string()),
                            span,
                            body_span,
                            calls,
                        },
                    );
                    self.function_index
                        .by_name
                        .entry(name.clone())
                        .or_default()
                        .push(fid);
                    self.function_index
                        .by_container_name
                        .insert((container_name.to_string(), name), fid);
                    self.index_statements(fid);
                }

                cursor = end;
            }
        }
    }

    fn add_definition(
        &mut self,
        id: DefId,
        name: String,
        container: Option<String>,
        span: SourceSpan,
        signature_span: SourceSpan,
    ) {
        if is_container_kind(id.kind) {
            self.def_index.container_defs.insert(name.clone(), id);
        }
        if matches!(
            id.kind,
            DefinitionKind::Struct
                | DefinitionKind::Enum
                | DefinitionKind::Error
                | DefinitionKind::Event
                | DefinitionKind::UserDefinedValueType
        ) {
            self.type_index.type_defs.insert(id);
        }
        if id.kind == DefinitionKind::UsingDirective {
            self.using_index.using_defs.insert(id);
        }
        if let Some(container) = &container {
            self.def_index
                .members_by_container
                .entry(container.clone())
                .or_default()
                .push(id);
        }
        self.ref_index
            .providers_by_symbol
            .entry(name.clone())
            .or_default()
            .insert(id);
        self.def_index
            .by_name
            .entry(name.clone())
            .or_default()
            .push(id);
        self.def_index.defs.insert(
            id,
            Definition {
                id,
                name,
                container,
                span,
                signature_span,
            },
        );
    }

    fn name_for_span(
        &self,
        kind: DefinitionKind,
        source_id: SourceId,
        span: SourceSpan,
    ) -> Option<String> {
        if !matches!(kind, DefinitionKind::StateVariable | DefinitionKind::Constant) {
            return None;
        }
        self.span_text(source_id, span).and_then(read_variable_name)
    }

    fn index_statements(&mut self, function_id: FunctionId) {
        let Some(function) = self.function_index.functions.get(&function_id) else {
            return;
        };
        let Some(body_span) = function.body_span else {
            return;
        };
        let Some(body) = self.span_text(function.id.def_id.source_id, body_span) else {
            return;
        };
        let body = body.to_string();
        let mut statement_no = 0usize;
        for local in split_statement_spans(&body) {
            statement_no += 1;
            let text = &body[local.start..local.end];
            let kind = classify_statement(text);
            let id = StatementId {
                source_id: function.id.def_id.source_id,
                node_id: function.id.def_id.node_id + statement_no,
                enclosing_function: function_id,
                span: SourceSpan {
                    start: body_span.start + local.start,
                    end: body_span.start + local.end,
                },
                kind,
            };
            self.stmt_index.statements.insert(id, text.to_string());
        }
    }
}

pub fn is_container_kind(kind: DefinitionKind) -> bool {
    matches!(
        kind,
        DefinitionKind::Contract
            | DefinitionKind::AbstractContract
            | DefinitionKind::Interface
            | DefinitionKind::Library
    )
}

fn starts_container_or_function(kind: DefinitionKind) -> bool {
    is_container_kind(kind)
        || matches!(
            kind,
            DefinitionKind::Function
                | DefinitionKind::Modifier
                | DefinitionKind::Struct
                | DefinitionKind::Enum
        )
}

fn next_nonempty_line(text: &str, mut offset: usize) -> Option<(usize, usize, &str)> {
    while offset < text.len() {
        let line_end = text[offset..]
            .find('\n')
            .map(|idx| offset + idx + 1)
            .unwrap_or(text.len());
        let line = &text[offset..line_end];
        let trimmed = line.trim_start();
        if !trimmed.trim().is_empty() {
            return Some((offset, line_end, trimmed.trim_end()));
        }
        offset = line_end;
    }
    None
}

fn parse_definition_head(trimmed: &str) -> Option<(DefinitionKind, String)> {
    if trimmed.starts_with("constructor(") || trimmed.starts_with("constructor ") {
        return Some((DefinitionKind::Function, "constructor".to_string()));
    }
    if trimmed.starts_with("fallback(") || trimmed.starts_with("fallback ") {
        return Some((DefinitionKind::Function, "fallback".to_string()));
    }
    if trimmed.starts_with("receive(") || trimmed.starts_with("receive ") {
        return Some((DefinitionKind::Function, "receive".to_string()));
    }
    let probes = [
        ("abstract contract ", DefinitionKind::AbstractContract),
        ("contract ", DefinitionKind::Contract),
        ("interface ", DefinitionKind::Interface),
        ("library ", DefinitionKind::Library),
        ("function ", DefinitionKind::Function),
        ("modifier ", DefinitionKind::Modifier),
        ("struct ", DefinitionKind::Struct),
        ("enum ", DefinitionKind::Enum),
        ("error ", DefinitionKind::Error),
        ("event ", DefinitionKind::Event),
        ("type ", DefinitionKind::UserDefinedValueType),
    ];
    for (prefix, kind) in probes {
        if let Some(rest) = trimmed.strip_prefix(prefix) {
            return read_identifier(rest).map(|name| (kind, name.to_string()));
        }
    }
    if looks_like_state_variable(trimmed) {
        return read_variable_name(trimmed).map(|name| (DefinitionKind::StateVariable, name));
    }
    None
}

fn read_identifier(rest: &str) -> Option<&str> {
    let rest = rest.trim_start();
    let end = rest
        .find(|ch: char| !(ch.is_ascii_alphanumeric() || ch == '_'))
        .unwrap_or(rest.len());
    if end == 0 {
        None
    } else {
        Some(&rest[..end])
    }
}

fn looks_like_state_variable(trimmed: &str) -> bool {
    if starts_with_visibility_or_storage_modifier(trimmed) {
        return false;
    }

    !trimmed.starts_with("return ")
        && !trimmed.starts_with("if ")
        && !trimmed.starts_with("for ")
        && !trimmed.starts_with("while ")
        && !trimmed.starts_with("emit ")
        && !trimmed.starts_with("revert ")
        && !trimmed.contains(" function ")
        && (trimmed.starts_with("mapping(")
            || trimmed.contains(" public ")
            || trimmed.contains(" internal ")
            || trimmed.contains(" private ")
            || trimmed.contains(" constant ")
            || trimmed.contains(" immutable ")
            || trimmed.ends_with(';'))
}

fn starts_with_visibility_or_storage_modifier(trimmed: &str) -> bool {
    let first = trimmed.split_whitespace().next().unwrap_or_default();
    matches!(
        first,
        "public" | "private" | "internal" | "external" | "constant" | "immutable" | "override"
    )
}

fn read_variable_name(trimmed: &str) -> Option<String> {
    let before_eq = declaration_before_initializer(trimmed);
    before_eq
        .trim_end_matches(';')
        .split_whitespace()
        .last()
        .map(|name| {
            name.trim_matches(|ch: char| !ch.is_ascii_alphanumeric() && ch != '_')
                .to_string()
        })
        .filter(|name| !name.is_empty())
}

fn declaration_before_initializer(trimmed: &str) -> &str {
    let bytes = trimmed.as_bytes();
    let mut paren_depth = 0usize;
    let mut bracket_depth = 0usize;
    let mut idx = 0usize;
    while idx < bytes.len() {
        match bytes[idx] {
            b'(' => paren_depth += 1,
            b')' => paren_depth = paren_depth.saturating_sub(1),
            b'[' => bracket_depth += 1,
            b']' => bracket_depth = bracket_depth.saturating_sub(1),
            b'=' if paren_depth == 0 && bracket_depth == 0 => return &trimmed[..idx],
            _ => {}
        }
        idx += 1;
    }
    trimmed
}

fn using_name(trimmed: &str) -> Option<String> {
    let rest = trimmed.strip_prefix("using ")?;
    Some(rest.trim_end_matches(';').trim().to_string())
}

fn find_semicolon_end(text: &str, start: usize) -> Option<usize> {
    text[start..].find(';').map(|idx| start + idx + 1)
}

fn find_signature_end(text: &str, start: usize, end: usize) -> usize {
    let slice = &text[start..end];
    let brace = slice.find('{').map(|idx| start + idx + 1);
    let semi = slice.find(';').map(|idx| start + idx + 1);
    match (brace, semi) {
        (Some(a), Some(b)) => a.min(b),
        (Some(a), None) => a,
        (None, Some(b)) => b,
        (None, None) => end,
    }
}

fn find_balanced_item_end(text: &str, start: usize) -> Option<usize> {
    let bytes = text.as_bytes();
    let mut idx = start;
    while idx < bytes.len() && bytes[idx] != b'{' && bytes[idx] != b';' {
        idx += 1;
    }
    if idx >= bytes.len() {
        return None;
    }
    if bytes[idx] == b';' {
        return Some(idx + 1);
    }
    let mut depth = 0i32;
    let mut in_string: Option<u8> = None;
    while idx < bytes.len() {
        let b = bytes[idx];
        if let Some(quote) = in_string {
            if b == b'\\' {
                idx += 2;
                continue;
            }
            if b == quote {
                in_string = None;
            }
            idx += 1;
            continue;
        }
        if b == b'/' && idx + 1 < bytes.len() && bytes[idx + 1] == b'/' {
            idx += 2;
            while idx < bytes.len() && bytes[idx] != b'\n' {
                idx += 1;
            }
            continue;
        }
        if b == b'/' && idx + 1 < bytes.len() && bytes[idx + 1] == b'*' {
            idx += 2;
            while idx + 1 < bytes.len() && !(bytes[idx] == b'*' && bytes[idx + 1] == b'/') {
                idx += 1;
            }
            idx = (idx + 2).min(bytes.len());
            continue;
        }
        if b == b'"' || b == b'\'' {
            in_string = Some(b);
        } else if b == b'{' {
            depth += 1;
        } else if b == b'}' {
            depth -= 1;
            if depth == 0 {
                return Some(idx + 1);
            }
        }
        idx += 1;
    }
    None
}

fn find_body_span(function_text: &str) -> Option<SourceSpan> {
    let start = function_text.find('{')? + 1;
    let end = function_text.rfind('}')?;
    Some(SourceSpan { start, end })
}

fn split_statement_spans(body: &str) -> Vec<SourceSpan> {
    let mut spans = Vec::new();
    let mut start = 0usize;
    let mut brace_depth = 0i32;
    let mut paren_depth = 0i32;
    let mut bracket_depth = 0i32;
    let mut in_string: Option<char> = None;
    let mut prev_was_escape = false;
    for (idx, ch) in body.char_indices() {
        if let Some(quote) = in_string {
            if ch == quote && !prev_was_escape {
                in_string = None;
            }
            prev_was_escape = ch == '\\' && !prev_was_escape;
            continue;
        }
        match ch {
            '"' | '\'' => {
                in_string = Some(ch);
                prev_was_escape = false;
            }
            '(' => paren_depth += 1,
            ')' => {
                if paren_depth > 0 {
                    paren_depth -= 1;
                }
            }
            '[' => bracket_depth += 1,
            ']' => {
                if bracket_depth > 0 {
                    bracket_depth -= 1;
                }
            }
            '{' => brace_depth += 1,
            '}' => {
                if brace_depth > 0 {
                    brace_depth -= 1;
                }
                if brace_depth == 0 && paren_depth == 0 && bracket_depth == 0 {
                    let end = idx + ch.len_utf8();
                    if body[start..end].trim().len() > 1 {
                        spans.push(SourceSpan { start, end });
                    }
                    start = end;
                }
            }
            ';' if brace_depth == 0 && paren_depth == 0 && bracket_depth == 0 => {
                let end = idx + 1;
                if !body[start..end].trim().is_empty() {
                    spans.push(SourceSpan { start, end });
                }
                start = end;
            }
            _ => {}
        }
    }
    spans
}

fn classify_statement(text: &str) -> StatementKind {
    let trimmed = text.trim_start();
    if trimmed.starts_with("return ") || trimmed == "return;" {
        StatementKind::Return
    } else if trimmed.starts_with("if ") || trimmed.starts_with("if(") {
        StatementKind::If
    } else if trimmed.starts_with("for ") || trimmed.starts_with("for(") {
        StatementKind::For
    } else if trimmed.starts_with("while ") || trimmed.starts_with("while(") {
        StatementKind::While
    } else if trimmed.starts_with("try ") {
        StatementKind::TryCatch
    } else if trimmed.starts_with("emit ") {
        StatementKind::Emit
    } else if trimmed.starts_with("revert ") || trimmed.starts_with("revert(") {
        StatementKind::Revert
    } else if trimmed.starts_with("assembly ") {
        StatementKind::Assembly
    } else if trimmed.contains('=') || trimmed.contains(" memory ") || trimmed.contains(" storage ")
    {
        StatementKind::VariableDeclaration
    } else {
        StatementKind::ExpressionStatement
    }
}

fn extract_call_names(text: &str) -> HashSet<String> {
    let mut calls = HashSet::new();
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
            if look < bytes.len() && bytes[look] == b'(' && !SOLIDITY_KEYWORDS.contains(&ident) {
                calls.insert(ident.to_string());
            }
        } else {
            idx += 1;
        }
    }
    calls
}

const SOLIDITY_KEYWORDS: &[&str] = &[
    "if", "for", "while", "return", "require", "assert", "revert", "emit", "new", "delete",
    "mapping", "function", "modifier", "event", "error",
];

fn parse_inheritance(signature: &str) -> Option<Vec<String>> {
    let (_, rest) = signature.split_once(" is ")?;
    let before_brace = rest.split('{').next().unwrap_or(rest);
    let bases = before_brace
        .split(',')
        .filter_map(|part| read_identifier(part.trim()))
        .map(|name| name.to_string())
        .collect::<Vec<_>>();
    Some(bases)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn source_db_indexes_adjacent_std_cheats_structs() {
        let db = SourceDatabase::build(&[PathBuf::from("examples/src/poc_final.t.sol")])
            .expect("source database should build fixture");
        let tx1559 = db
            .providers_for_symbol("Tx1559")
            .into_iter()
            .find(|id| id.kind == DefinitionKind::Struct)
            .expect("Tx1559 struct should be indexed");
        let text = db
            .get_source_text(tx1559)
            .expect("Tx1559 source text should be available");
        assert!(text.trim_start().starts_with("struct Tx1559 {"), "{text}");
        assert!(text.contains("Tx1559Detail txDetail;"), "{text}");
        assert!(!text.trim_start().starts_with("struct Tx1559Detail {"), "{text}");
    }

    #[test]
    fn source_db_indexes_multiline_state_variable_as_single_definition() {
        let db = SourceDatabase::build(&[PathBuf::from("examples/src/poc_final.t.sol")])
            .expect("source database should build fixture");
        let approved = db
            .providers_for_symbol("isApprovedForAll")
            .into_iter()
            .find(|id| id.kind == DefinitionKind::StateVariable)
            .expect("isApprovedForAll storage variable should be indexed");
        let text = db
            .get_source_text(approved)
            .expect("isApprovedForAll source text should be available");
        assert!(text.trim_start().starts_with("mapping("), "{text}");
        assert!(text.contains("public isApprovedForAll;"), "{text}");
        assert!(!text.trim_start().starts_with("public "), "{text}");
    }
}
