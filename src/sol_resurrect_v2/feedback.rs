use super::fallback::FallbackLevel;
use super::source_db::SourceDatabase;
use super::validator::{CompileErrorKind, V2CompileError};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FeedbackAction {
    AddSymbol(String),
    AddMember {
        receiver_type: Option<String>,
        member: String,
    },
    WidenSyntax,
    WidenContainer,
    Noop,
}

pub struct FeedbackController<'a> {
    source_db: &'a SourceDatabase,
}

impl<'a> FeedbackController<'a> {
    pub fn new(source_db: &'a SourceDatabase) -> Self {
        Self { source_db }
    }

    pub fn analyze(&self, errors: &[V2CompileError], _level: FallbackLevel) -> FeedbackAction {
        for err in errors {
            if let Some((receiver_type, member)) = extract_missing_implementation(&err.message) {
                return FeedbackAction::AddMember {
                    receiver_type: Some(receiver_type),
                    member,
                };
            }
            if let Some((receiver_type, member)) = extract_runtime_missing_member(&err.message) {
                return FeedbackAction::AddMember {
                    receiver_type: Some(receiver_type),
                    member,
                };
            }
            match err.kind {
                CompileErrorKind::MissingSymbol => {
                    if let Some(symbol) = extract_missing_symbol(&err.message)
                        .or_else(|| self.resolve_symbol_from_message(&err.message))
                    {
                        return FeedbackAction::AddSymbol(symbol);
                    }
                }
                CompileErrorKind::MemberNotFound => {
                    if let Some((receiver_type, member)) = extract_missing_member(&err.message) {
                        return FeedbackAction::AddMember {
                            receiver_type,
                            member,
                        };
                    }
                }
                CompileErrorKind::Syntax => {
                    return FeedbackAction::WidenSyntax;
                }
                CompileErrorKind::InheritanceConflict
                | CompileErrorKind::DuplicateDefinition
                | CompileErrorKind::OverrideConflict => {
                    return FeedbackAction::WidenContainer;
                }
                _ => {}
            }
        }
        FeedbackAction::Noop
    }

    fn resolve_symbol_from_message(&self, message: &str) -> Option<String> {
        let mut candidates = message
            .split(|ch: char| !(ch.is_ascii_alphanumeric() || ch == '_'))
            .filter(|token| !token.is_empty())
            .filter(|token| !NOISY_TOKENS.contains(token))
            .collect::<Vec<_>>();
        candidates.reverse();
        for token in candidates {
            if !self.source_db.providers_for_symbol(token).is_empty() {
                return Some(token.to_string());
            }
        }
        None
    }
}

const NOISY_TOKENS: &[&str] = &[
    "Error",
    "Identifier",
    "not",
    "found",
    "or",
    "unique",
    "Relevant",
    "source",
    "part",
    "starts",
    "here",
    "and",
    "spans",
    "across",
    "multiple",
    "lines",
    "contract",
    "abstract",
    "interface",
    "library",
    "is",
];

fn extract_missing_symbol(message: &str) -> Option<String> {
    if let Some(symbol) = symbol_under_caret(message) {
        return Some(symbol);
    }
    for marker in [
        "Undeclared identifier",
        "Identifier not found or not unique",
    ] {
        if let Some(idx) = message.find(marker) {
            let rest = &message[idx + marker.len()..];
            let rest = rest.trim_start_matches(|ch: char| ch == ':' || ch.is_whitespace());
            if let Some(symbol) = read_identifier(rest) {
                return Some(symbol);
            }
        }
    }
    None
}

fn extract_missing_member(message: &str) -> Option<(Option<String>, String)> {
    let lower = message.to_lowercase();
    if !lower.contains("member") || !lower.contains("not found") {
        return None;
    }
    let member = quoted_token(message).or_else(|| {
        message
            .split_whitespace()
            .find(|part| {
                part.chars()
                    .all(|ch| ch.is_ascii_alphanumeric() || ch == '_')
            })
            .map(|part| part.to_string())
    })?;
    let receiver_type = message.split(" in ").nth(1).and_then(read_receiver_type);
    Some((receiver_type, member))
}

fn extract_missing_implementation(message: &str) -> Option<(String, String)> {
    let lower = message.to_ascii_lowercase();
    if !lower.contains("should be marked as abstract") || !lower.contains("missing implementation")
    {
        return None;
    }
    let contract_marker = "Contract \"";
    let contract_start = message.find(contract_marker)? + contract_marker.len();
    let contract_end = message[contract_start..].find('"')? + contract_start;
    let contract = message[contract_start..contract_end].to_string();

    let implementation_start = lower.find("missing implementation")?;
    let after = &message[implementation_start..];
    let function_marker = "function ";
    let function_start = after.find(function_marker)? + function_marker.len();
    let member = read_identifier(&after[function_start..])?;
    Some((contract, member))
}

fn extract_runtime_missing_member(message: &str) -> Option<(String, String)> {
    if !message.contains("unrecognized function selector") {
        return None;
    }
    for line in message.lines().rev() {
        let trimmed = line.trim();
        let Some(rest) = trimmed.strip_prefix("at ") else {
            continue;
        };
        let (receiver, member) = rest.split_once('.')?;
        let receiver = read_identifier(receiver)?;
        let member = read_identifier(member)?;
        return Some((receiver, member));
    }
    None
}

fn read_receiver_type(rest: &str) -> Option<String> {
    let trimmed = rest.trim();
    for marker in ["type(contract ", "type(library ", "type(interface "] {
        if let Some(after) = trimmed.strip_prefix(marker) {
            return read_identifier(after);
        }
    }
    for marker in ["contract ", "library ", "interface "] {
        if let Some(after) = trimmed.strip_prefix(marker) {
            return read_identifier(after);
        }
    }
    read_identifier(trimmed)
}

fn quoted_token(message: &str) -> Option<String> {
    let start = message.find('"')?;
    let end = message[start + 1..].find('"')?;
    Some(message[start + 1..start + 1 + end].to_string())
}

fn read_identifier(rest: &str) -> Option<String> {
    let trimmed = rest.trim_start();
    let trimmed = trimmed.trim_start_matches(&['"', '\'', '`'][..]);
    let end = trimmed
        .find(|ch: char| !(ch.is_ascii_alphanumeric() || ch == '_'))
        .unwrap_or(trimmed.len());
    if end == 0 {
        None
    } else {
        Some(trimmed[..end].to_string())
    }
}

fn symbol_under_caret(message: &str) -> Option<String> {
    let mut previous = None::<&str>;
    for line in message.lines() {
        if line.trim_start().starts_with('|') && line.contains('^') {
            let caret_part = line
                .split_once('|')
                .map(|(_, rest)| rest.strip_prefix(' ').unwrap_or(rest))
                .unwrap_or(line);
            let caret_start = caret_part.find('^')?;
            let snippet = previous?;
            let start = caret_start.min(snippet.len());
            let bytes = snippet.as_bytes();
            let mut left = start;
            while left > 0 && (bytes[left - 1].is_ascii_alphanumeric() || bytes[left - 1] == b'_') {
                left -= 1;
            }
            let mut right = start;
            while right < bytes.len()
                && (bytes[right].is_ascii_alphanumeric() || bytes[right] == b'_')
            {
                right += 1;
            }
            if left < right {
                return Some(snippet[left..right].to_string());
            }
        } else if !line.trim().is_empty() {
            previous = Some(line);
        }
    }
    None
}
