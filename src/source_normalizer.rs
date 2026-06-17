use std::collections::HashSet;

#[derive(Debug, Clone)]
pub enum NormalizationActionKind {
    DroppedBlockComment,
    DroppedOrphanComment,
    DroppedSectionLabel,
    DroppedImportOrPragma,
    DroppedNatSpecFragment,
}

#[derive(Debug, Clone)]
pub struct NormalizationAction {
    pub line: usize,
    pub kind: NormalizationActionKind,
    pub text: String,
}

#[derive(Debug, Clone, Default)]
pub struct NormalizationReport {
    pub actions: Vec<NormalizationAction>,
}

impl NormalizationReport {
    pub fn has_changes(&self) -> bool {
        !self.actions.is_empty()
    }
}

#[derive(Debug, Clone)]
pub struct NormalizedSource {
    pub code: String,
    pub report: NormalizationReport,
}

pub fn normalize_source(code: &str) -> NormalizedSource {
    SourceNormalizer::default().normalize(code)
}

pub fn normalize_solidity_fragment(code: &str) -> String {
    dedupe_top_level_definitions(&normalize_source(code).code)
}

pub fn first_suspicious_line(code: &str) -> Option<(usize, &str)> {
    code.lines().enumerate().find_map(|(idx, line)| {
        let trimmed = line.trim();
        if is_removable_residue_line(trimmed) {
            Some((idx + 1, line))
        } else {
            None
        }
    })
}

pub fn top_level_definition_names(code: &str) -> HashSet<String> {
    let mut names = HashSet::new();
    let mut depth = 0i32;
    for line in code.lines() {
        if depth == 0 {
            if let Some((_, name)) = parse_top_level_definition(line.trim_start()) {
                names.insert(name.to_string());
            }
        }

        depth += line.matches('{').count() as i32;
        depth -= line.matches('}').count() as i32;
        if depth < 0 {
            depth = 0;
        }
    }
    names
}

fn top_level_definition_keys(code: &str) -> Vec<String> {
    let mut keys = Vec::new();
    let mut depth = 0i32;

    for line in code.lines() {
        if depth == 0 {
            if let Some((kind, name)) = parse_top_level_definition(line.trim_start()) {
                if kind != "function" {
                    keys.push(format!("{}:{}", kind, name));
                }
            }
        }

        depth += line.matches('{').count() as i32;
        depth -= line.matches('}').count() as i32;
        if depth < 0 {
            depth = 0;
        }
    }

    keys
}

pub fn split_top_level_chunks(code: &str) -> Vec<String> {
    let mut chunks = Vec::new();
    let mut current = Vec::new();
    let mut depth = 0i32;

    for line in code.lines() {
        let trimmed = line.trim_start();
        let starts_top_level_item = depth == 0 && parse_top_level_definition(trimmed).is_some();

        if starts_top_level_item && !current.is_empty() {
            push_nonempty_chunk(&mut chunks, &current);
            current.clear();
        }

        current.push(line.to_string());
        depth += line.matches('{').count() as i32;
        depth -= line.matches('}').count() as i32;
        if depth < 0 {
            depth = 0;
        }

        if depth == 0
            && !current.is_empty()
            && (trimmed.starts_with("type ") || trimmed.starts_with("error "))
            && trimmed.ends_with(';')
        {
            push_nonempty_chunk(&mut chunks, &current);
            current.clear();
        }
    }

    if !current.is_empty() {
        push_nonempty_chunk(&mut chunks, &current);
    }

    chunks
}

fn push_nonempty_chunk(chunks: &mut Vec<String>, lines: &[String]) {
    if lines.iter().any(|line| !line.trim().is_empty()) {
        chunks.push(lines.join("\n"));
    }
}

pub fn looks_parse_worthy(code: &str) -> bool {
    code.lines()
        .any(|line| parse_top_level_definition(line.trim_start()).is_some())
}

pub fn dedupe_top_level_definitions(code: &str) -> String {
    let mut seen = HashSet::new();
    let mut kept = Vec::new();

    for chunk in split_top_level_chunks(code) {
        let keys = top_level_definition_keys(&chunk);
        if keys.is_empty() {
            kept.push(chunk);
            continue;
        }

        if keys.iter().any(|key| seen.contains(key)) {
            continue;
        }

        for key in keys {
            seen.insert(key);
        }
        kept.push(chunk);
    }

    kept.join("\n\n")
}

pub fn parse_top_level_definition(line: &str) -> Option<(&'static str, &str)> {
    let keywords = [
        "contract",
        "abstract contract",
        "interface",
        "library",
        "struct",
        "enum",
        "error",
        "type",
        "function",
    ];

    for keyword in keywords {
        let prefix = format!("{} ", keyword);
        if let Some(rest) = line.strip_prefix(&prefix) {
            let name = rest
                .split(|c: char| c.is_whitespace() || c == '{' || c == '(' || c == ';')
                .next()
                .unwrap_or("");
            if !name.is_empty() {
                return Some((keyword, name));
            }
        }
    }

    None
}

#[derive(Debug, Clone)]
pub struct SourceNormalizer {
    drop_imports_and_pragmas: bool,
}

impl Default for SourceNormalizer {
    fn default() -> Self {
        Self {
            drop_imports_and_pragmas: false,
        }
    }
}

impl SourceNormalizer {
    pub fn for_llm_fragment() -> Self {
        Self {
            drop_imports_and_pragmas: true,
        }
    }

    pub fn normalize(&self, code: &str) -> NormalizedSource {
        let mut out = Vec::new();
        let mut report = NormalizationReport::default();
        let mut in_block_comment = false;
        let lines: Vec<&str> = code.lines().collect();

        for (idx, line) in lines.iter().enumerate() {
            let line_no = idx + 1;
            let trimmed = line.trim();

            if in_block_comment {
                report.actions.push(action(
                    line_no,
                    NormalizationActionKind::DroppedBlockComment,
                    line,
                ));
                if trimmed.contains("*/") {
                    in_block_comment = false;
                }
                continue;
            }

            if self.drop_imports_and_pragmas
                && (trimmed.starts_with("pragma solidity") || trimmed.starts_with("import "))
            {
                report.actions.push(action(
                    line_no,
                    NormalizationActionKind::DroppedImportOrPragma,
                    line,
                ));
                continue;
            }

            if trimmed.starts_with("/*") || trimmed.starts_with("/**") {
                report.actions.push(action(
                    line_no,
                    NormalizationActionKind::DroppedBlockComment,
                    line,
                ));
                if !trimmed.contains("*/") {
                    in_block_comment = true;
                }
                continue;
            }

            if is_orphan_comment_line(trimmed) {
                report.actions.push(action(
                    line_no,
                    NormalizationActionKind::DroppedOrphanComment,
                    line,
                ));
                continue;
            }

            // Tier 1.2: Detect NatSpec fragments (@dev, @param, @notice, etc.)
            // and formula/prose descriptions that leak into function bodies
            if is_natspec_fragment(trimmed) {
                report.actions.push(action(
                    line_no,
                    NormalizationActionKind::DroppedNatSpecFragment,
                    line,
                ));
                continue;
            }

            let previous = previous_nonempty_line(&lines, idx);
            let next = next_nonempty_line(&lines, idx);

            if looks_like_ascii_diagram_fragment(
                trimmed,
                previous,
                next,
                has_nearby_ascii_diagram_context(&lines, idx),
            ) {
                report.actions.push(action(
                    line_no,
                    NormalizationActionKind::DroppedOrphanComment,
                    line,
                ));
                continue;
            }

            if looks_like_code_continuation(trimmed, previous, next) {
                out.push(normalize_inline_identifier_comment(line));
                continue;
            }

            if is_bare_section_label(trimmed, previous, next) {
                report.actions.push(action(
                    line_no,
                    NormalizationActionKind::DroppedSectionLabel,
                    line,
                ));
                continue;
            }

            if looks_like_orphan_block_comment_body(trimmed, previous, next) {
                report.actions.push(action(
                    line_no,
                    NormalizationActionKind::DroppedOrphanComment,
                    line,
                ));
                continue;
            }

            out.push(normalize_inline_identifier_comment(line));
        }

        let code = drop_invalid_top_level_fragments(&out.join("\n"));

        NormalizedSource { code, report }
    }
}

fn drop_invalid_top_level_fragments(code: &str) -> String {
    let lines: Vec<&str> = code.lines().collect();
    let mut out = Vec::new();
    let mut depth = 0i32;
    let mut idx = 0usize;

    while idx < lines.len() {
        let line = lines[idx];

        if depth == 0 && starts_invalid_top_level_fragment(&lines, idx) {
            idx += 1;
            while idx < lines.len() {
                let candidate = lines[idx].trim_start();
                if starts_major_top_level_container(candidate)
                    || starts_minor_top_level_item(candidate)
                    || starts_top_level_free_function(candidate)
                {
                    break;
                }
                idx += 1;
            }
            continue;
        }

        out.push(line.to_string());
        depth += line.matches('{').count() as i32;
        depth -= line.matches('}').count() as i32;
        if depth < 0 {
            depth = 0;
        }
        idx += 1;
    }

    out.join("\n")
}

fn starts_invalid_top_level_fragment(lines: &[&str], idx: usize) -> bool {
    let trimmed = lines[idx].trim_start();
    if trimmed.is_empty()
        || trimmed.starts_with("//")
        || trimmed.starts_with("/*")
        || starts_major_top_level_container(trimmed)
        || starts_minor_top_level_item(trimmed)
    {
        return false;
    }

    if trimmed.starts_with(')') || trimmed.starts_with('.') || trimmed.starts_with(',') {
        return true;
    }

    if trimmed.starts_with("if ")
        || trimmed.starts_with("else ")
        || trimmed.starts_with("for ")
        || trimmed.starts_with("while ")
        || trimmed.starts_with("return ")
        || trimmed.starts_with("revert ")
        || trimmed.starts_with("unchecked ")
        || trimmed.starts_with("assembly ")
    {
        return true;
    }

    looks_like_invalid_container_prose(trimmed)
        || looks_like_prose_residue(trimmed)
        || (trimmed.starts_with("function ") && top_level_function_has_visibility(lines, idx))
}

fn starts_top_level_free_function(trimmed: &str) -> bool {
    trimmed.starts_with("function ")
        && ![" internal", " external", " public", " private"]
            .iter()
            .any(|visibility| trimmed.contains(visibility))
}

fn starts_major_top_level_container(trimmed: &str) -> bool {
    let keywords = ["abstract contract", "contract", "interface", "library"];
    for keyword in keywords {
        let prefix = format!("{} ", keyword);
        let Some(rest) = trimmed.strip_prefix(&prefix) else {
            continue;
        };
        let name = rest
            .split(|c: char| c.is_whitespace() || c == '{')
            .next()
            .unwrap_or("");
        if !is_solidity_identifier(name) {
            return false;
        }
        let after_name = rest[name.len()..].trim_start();
        return after_name.is_empty()
            || after_name.starts_with('{')
            || after_name.starts_with("is ");
    }
    false
}

fn looks_like_invalid_container_prose(trimmed: &str) -> bool {
    let keywords = ["abstract contract", "contract", "interface", "library"];
    for keyword in keywords {
        let prefix = format!("{} ", keyword);
        let Some(rest) = trimmed.strip_prefix(&prefix) else {
            continue;
        };
        let name = rest
            .split(|c: char| c.is_whitespace() || c == '{')
            .next()
            .unwrap_or("");
        let after_name = rest[name.len()..].trim_start();
        if name.is_empty()
            || after_name.is_empty()
            || after_name.starts_with('{')
            || after_name.starts_with("is ")
        {
            return false;
        }

        let word_count = trimmed
            .split_whitespace()
            .filter(|word| word.chars().any(|c| c.is_ascii_alphabetic()))
            .count();
        let has_lowercase = trimmed.chars().any(|c| c.is_ascii_lowercase());
        let has_prose_punctuation = trimmed.contains(',')
            || trimmed.contains(':')
            || trimmed.ends_with('.')
            || trimmed.contains(" and ")
            || trimmed.contains(" for ")
            || trimmed.contains(" the ");

        if word_count >= 4
            && has_lowercase
            && has_prose_punctuation
            && !trimmed.contains(';')
            && !trimmed.contains('{')
            && !trimmed.contains('}')
        {
            return true;
        }
    }
    false
}

fn is_solidity_identifier(name: &str) -> bool {
    let mut chars = name.chars();
    let Some(first) = chars.next() else {
        return false;
    };
    (first == '_' || first.is_ascii_alphabetic())
        && chars.all(|ch| ch == '_' || ch.is_ascii_alphanumeric())
}

fn starts_minor_top_level_item(trimmed: &str) -> bool {
    trimmed.starts_with("pragma ")
        || trimmed.starts_with("import ")
        || trimmed.starts_with("using ")
        || trimmed.starts_with("type ")
        || trimmed.starts_with("struct ")
        || trimmed.starts_with("enum ")
        || trimmed.starts_with("error ")
}

fn top_level_function_has_visibility(lines: &[&str], idx: usize) -> bool {
    let mut signature = String::new();
    for line in lines.iter().skip(idx).take(20) {
        signature.push(' ');
        signature.push_str(line.trim());
        if line.contains('{') || line.trim_end().ends_with(';') {
            break;
        }
    }

    [" internal", " external", " public", " private"]
        .iter()
        .any(|visibility| signature.contains(visibility))
}

fn normalize_inline_identifier_comment(line: &str) -> String {
    let Some(start) = line.find("/*") else {
        return line.to_string();
    };
    let Some(end_rel) = line[start + 2..].find("*/") else {
        return line.to_string();
    };

    let end = start + 2 + end_rel;
    let comment = line[start + 2..end].trim();
    if !is_identifier(comment) {
        return line.to_string();
    }

    let mut normalized = String::new();
    normalized.push_str(&line[..start]);
    normalized.push_str(comment);
    normalized.push_str(&line[end + 2..]);
    normalized
}

fn is_identifier(value: &str) -> bool {
    let mut chars = value.chars();
    let Some(first) = chars.next() else {
        return false;
    };
    (first.is_ascii_alphabetic() || first == '_')
        && chars.all(|ch| ch.is_ascii_alphanumeric() || ch == '_')
}

fn looks_like_code_continuation(trimmed: &str, prev: Option<&str>, next: Option<&str>) -> bool {
    if trimmed.is_empty() || looks_like_solidity_statement(trimmed) {
        return false;
    }
    let value = trimmed.strip_prefix("? ").unwrap_or(trimmed);
    let identifier_like = value
        .chars()
        .all(|ch| ch.is_ascii_uppercase() || ch.is_ascii_digit() || ch == '_')
        && value.chars().any(|ch| ch.is_ascii_alphabetic());
    if !identifier_like {
        return false;
    }

    let prev_supports = prev
        .map(|line| {
            let trimmed = line.trim_end();
            trimmed.ends_with(',') || trimmed.ends_with('(') || trimmed.ends_with('?')
        })
        .unwrap_or(false);
    let next_supports = next
        .map(|line| {
            let trimmed = line.trim_start();
            trimmed.starts_with(");")
                || trimmed.starts_with(',')
                || trimmed.starts_with(':')
                || trimmed.ends_with(',')
        })
        .unwrap_or(false);

    prev_supports || next_supports
}

fn action(line: usize, kind: NormalizationActionKind, text: &str) -> NormalizationAction {
    NormalizationAction {
        line,
        kind,
        text: text.trim().to_string(),
    }
}

pub fn is_removable_residue_line(trimmed: &str) -> bool {
    is_orphan_comment_line(trimmed)
        || is_bare_section_label(trimmed, None, None)
        || looks_like_ascii_art_residue(trimmed)
        || looks_like_prose_residue(trimmed)
        || is_natspec_fragment(trimmed)
}

/// Detect NatSpec documentation fragments that have leaked into code.
/// These are lines like:
///   `@dev Standard math utilities missing in the Solidity language.`
///   `Diagrams shown for currency0, and applies for currency1 the same`
///   `Short put BPR = 100% - (price/strike) + SCR`
///   `from the msg.sender to the Uniswap V4 pool:`
fn is_natspec_fragment(trimmed: &str) -> bool {
    // Definite NatSpec tags — always drop
    if trimmed.starts_with("@dev ")
        || trimmed.starts_with("@param ")
        || trimmed.starts_with("@return ")
        || trimmed.starts_with("@notice ")
        || trimmed.starts_with("@inheritdoc ")
        || trimmed.starts_with("@custom:")
        || trimmed.starts_with("@title ")
        || trimmed.starts_with("@author ")
    {
        return true;
    }

    if trimmed.starts_with("let ") || trimmed.contains(":=") {
        return false;
    }

    // Prose-heavy lines that contain formula-like content but are clearly descriptions
    // These pass through `looks_like_solidity_statement` because they contain '=' or '()'
    // but are actually NatSpec descriptions, not code.
    if trimmed.len() < 15 || trimmed.len() > 200 {
        return false;
    }

    // Count word-like tokens (space separated)
    let words: Vec<&str> = trimmed.split_whitespace().collect();
    let word_count = words.len();
    if word_count < 4 {
        return false;
    }

    // If the line has lowercase English words and no semicolons, it's likely prose
    let has_lowercase_words = words
        .iter()
        .any(|w| w.len() >= 3 && w.chars().all(|c| c.is_ascii_lowercase()));
    let has_semicolon = trimmed.contains(';');
    let has_braces = trimmed.contains('{') || trimmed.contains('}');

    // Heuristic: lines with many English words, no semicolons, no braces
    // are likely NatSpec descriptions even if they contain '=' or '()'
    if has_lowercase_words && !has_semicolon && !has_braces && word_count >= 5 {
        if trimmed.contains(" memory ")
            || trimmed.contains(" storage ")
            || trimmed.contains(" calldata ")
            || trimmed.contains('[')
            || trimmed.contains(']')
            || trimmed.contains(" = ")
        {
            return false;
        }

        // Additional check: should not start with Solidity keywords
        let sol_keywords = [
            "contract ",
            "library ",
            "interface ",
            "function ",
            "modifier ",
            "event ",
            "struct ",
            "enum ",
            "type ",
            "using ",
            "return ",
            "returns ",
            "returns(",
            "if ",
            "for ",
            "while ",
            "revert ",
            "require(",
            "emit ",
            "mapping(",
            "address ",
            "uint",
            "int",
            "bool ",
            "bytes",
            "string ",
        ];
        if !sol_keywords.iter().any(|kw| trimmed.starts_with(kw)) {
            return true;
        }
    }

    false
}

fn is_orphan_comment_line(trimmed: &str) -> bool {
    if trimmed.is_empty() {
        return false;
    }

    trimmed.starts_with('*')
        || trimmed.starts_with("*/")
        || trimmed.starts_with("/**")
        || is_decorative_comment_tail(trimmed)
}

fn is_decorative_comment_tail(trimmed: &str) -> bool {
    let meaningful = trimmed
        .chars()
        .filter(|c| !c.is_whitespace())
        .collect::<String>();

    !meaningful.is_empty()
        && meaningful.len() >= 4
        && meaningful
            .chars()
            .all(|c| matches!(c, '/' | '*' | '-' | '_' | '=' | '~'))
}

fn is_bare_section_label(trimmed: &str, prev: Option<&str>, next: Option<&str>) -> bool {
    if trimmed.is_empty() || trimmed.len() > 96 {
        return false;
    }

    let labels = [
        "MOCKS",
        "TESTS",
        "EVENTS",
        "ERRORS",
        "STORAGE",
        "CONSTRUCTOR",
        "TYPES",
        "LIBRARIES",
        "INTERFACES",
        "AUTH",
        "OVERRIDES",
        "QUERIES",
        "ACTIONS",
        "HELPERS",
        "CONFIG",
        "CONSTANTS",
        "IMMUTABLES",
        "METADATA STORAGE",
        "ERC20 STORAGE",
        "ERC20 LOGIC",
        "INTERNAL MINT/BURN LOGIC",
        "VAULT MANAGEMENT",
        "POOL-SPECIFIC IMMUTABLE PARAMETERS",
        "INITIALIZATION",
        "EIP SUPPORT",
        "QUERY HELPERS",
        "ONBOARD MEDIAN TWAP",
        "MINT/BURN INTERFACE",
        "POSITION MINTING LOGIC",
        "POSITION BURNING LOGIC",
        "SOLVENCY CHECKS",
        "AVAILABLE PREMIUM LOGIC",
        "SELL",
        "BUY",
        "COLLATERAL",
        "RATIO",
    ];

    labels.contains(&trimmed) || looks_like_orphan_section_heading(trimmed, prev, next)
}

fn looks_like_orphan_block_comment_body(
    trimmed: &str,
    prev: Option<&str>,
    next: Option<&str>,
) -> bool {
    if trimmed.is_empty() || looks_like_solidity_statement(trimmed) {
        return false;
    }

    looks_like_ascii_art_residue(trimmed)
        || (looks_like_prose_residue(trimmed)
            && (prev
                .map(line_supports_comment_residue_context)
                .unwrap_or(false)
                || next
                    .map(line_supports_comment_residue_context)
                    .unwrap_or(false)))
}

fn looks_like_ascii_art_residue(trimmed: &str) -> bool {
    if trimmed.is_empty() {
        return false;
    }

    if trimmed.chars().any(is_unicode_diagram_char) {
        return true;
    }

    let art_chars = trimmed
        .chars()
        .filter(|c| {
            matches!(c, '|' | '^' | '_' | '-' | '+' | '>' | '<' | '%' | '`') || *c == '\u{00AF}'
        })
        .count();
    art_chars >= 2
        || trimmed.ends_with('_')
        || trimmed.contains("--->")
        || trimmed.contains("_-")
        || trimmed.contains("- |")
}

/// True when the line looks like a doc-comment ASCII diagram label,
/// e.g. "L = lowerTick, U = upperTick" — comma-separated id=id pairs.
fn is_diagram_label_line(trimmed: &str) -> bool {
    if !trimmed.contains(',') || trimmed.contains(';') || starts_like_solidity_item(trimmed) {
        return false;
    }
    let parts: Vec<&str> = trimmed.split(',').collect();
    if parts.len() < 2 {
        return false;
    }
    parts.iter().all(|p| {
        let p = p.trim();
        let segments: Vec<&str> = p.splitn(2, '=').collect();
        if segments.len() != 2 {
            return false;
        }
        let left = segments[0].trim();
        let right = segments[1].trim();
        let is_id = |s: &str| {
            !s.is_empty()
                && s.len() <= 48
                && s.chars().all(|c| c.is_ascii_alphanumeric() || c == '_')
        };
        is_id(left) && is_id(right)
    })
}

fn looks_like_ascii_diagram_fragment(
    trimmed: &str,
    prev: Option<&str>,
    next: Option<&str>,
    has_nearby_diagram_context: bool,
) -> bool {
    if trimmed.is_empty() || trimmed.contains(';') || trimmed.contains('{') || trimmed.contains('}')
    {
        return false;
    }

    if looks_like_ascii_art_residue(trimmed) {
        return true;
    }

    // Detect inline diagram labels like "L = lowerTick, U = upperTick"
    // — comma-separated identifier=identifier pairs with no semicolons.
    // These leak from doc-comment ASCII diagrams (e.g. V4StateReader).
    if is_diagram_label_line(trimmed) {
        return true;
    }

    // Detect short orphan identifiers (like "tick", "current") that are
    // ASCII diagram labels adjacent to a diagram-label line.
    if trimmed.len() <= 20
        && !trimmed.contains(';')
        && !trimmed.contains('(')
        && !trimmed.contains(')')
        && trimmed
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || c == '_')
        && !starts_like_solidity_item(trimmed)
    {
        let neighbor_is_label = has_nearby_diagram_context
            || prev
                .map(|p| is_diagram_label_line(p.trim()))
                .unwrap_or(false)
            || next
                .map(|n| is_diagram_label_line(n.trim()))
                .unwrap_or(false);
        if neighbor_is_label {
            return true;
        }
    }

    let has_diagram_neighbor = has_nearby_diagram_context
        || prev
            .map(|line| looks_like_ascii_art_residue(line.trim()))
            .unwrap_or(false)
        || next
            .map(|line| looks_like_ascii_art_residue(line.trim()))
            .unwrap_or(false);
    if !has_diagram_neighbor {
        return false;
    }

    let has_diagram_caption_shape = trimmed.contains(',')
        || trimmed.contains('=')
        || trimmed
            .chars()
            .all(|ch| ch.is_ascii_alphanumeric() || ch.is_whitespace() || ch == '_');

    has_diagram_caption_shape && !starts_like_solidity_item(trimmed)
}

fn has_nearby_ascii_diagram_context(lines: &[&str], idx: usize) -> bool {
    let mut seen = 0usize;
    for line in lines[..idx].iter().rev() {
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }
        if starts_like_solidity_item(trimmed) || trimmed.ends_with(';') || trimmed.ends_with('{') {
            break;
        }
        if looks_like_ascii_art_residue(trimmed) || is_diagram_label_line(trimmed) {
            return true;
        }
        seen += 1;
        if seen >= 5 {
            break;
        }
    }

    seen = 0;
    for line in lines.iter().skip(idx + 1) {
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }
        if starts_like_solidity_item(trimmed) || trimmed.ends_with(';') || trimmed.ends_with('{') {
            break;
        }
        if looks_like_ascii_art_residue(trimmed) || is_diagram_label_line(trimmed) {
            return true;
        }
        seen += 1;
        if seen >= 5 {
            break;
        }
    }

    false
}

fn is_unicode_diagram_char(ch: char) -> bool {
    matches!(
        ch,
        '▲' | '▼'
            | '◄'
            | '►'
            | '△'
            | '▽'
            | '←'
            | '→'
            | '↔'
            | '↑'
            | '↓'
            | '│'
            | '─'
            | '┌'
            | '┐'
            | '└'
            | '┘'
            | '├'
            | '┤'
            | '┬'
            | '┴'
            | '┼'
    )
}

fn starts_like_solidity_item(trimmed: &str) -> bool {
    [
        "contract ",
        "library ",
        "interface ",
        "function ",
        "modifier ",
        "event ",
        "error ",
        "struct ",
        "enum ",
        "type ",
        "using ",
        "return ",
        "if ",
        "else",
        "for ",
        "while ",
        "revert ",
        "require(",
        "emit ",
        "mapping(",
        "address ",
        "uint",
        "int",
        "bool ",
        "bytes",
        "string ",
    ]
    .iter()
    .any(|prefix| trimmed.starts_with(prefix))
}

fn looks_like_prose_residue(trimmed: &str) -> bool {
    if trimmed.len() < 12 || trimmed.len() > 140 {
        return false;
    }
    if looks_like_solidity_statement(trimmed) {
        return false;
    }

    let words = trimmed
        .split_whitespace()
        .filter(|word| word.chars().any(|c| c.is_ascii_alphabetic()))
        .count();
    let lowercase = trimmed.chars().any(|c| c.is_ascii_lowercase());
    let prose_punctuation = trimmed.contains(',')
        || trimmed.contains(':')
        || trimmed.contains(" and ")
        || trimmed.contains(" for ")
        || trimmed.contains(" the ");

    words >= 3 && lowercase && prose_punctuation
}

fn line_supports_comment_residue_context(line: &str) -> bool {
    let trimmed = line.trim();
    trimmed.is_empty()
        || is_orphan_comment_line(trimmed)
        || is_decorative_comment_tail(trimmed)
        || looks_like_ascii_art_residue(trimmed)
        || is_bare_section_label(trimmed, None, None)
}

fn looks_like_orphan_section_heading(
    trimmed: &str,
    prev: Option<&str>,
    next: Option<&str>,
) -> bool {
    if trimmed.len() < 6 {
        return false;
    }

    let mut alpha_count = 0usize;
    let mut has_separator = false;
    let mut word_count = 0usize;
    let mut in_word = false;
    for ch in trimmed.chars() {
        if ch.is_ascii_alphabetic() {
            if !ch.is_ascii_uppercase() {
                return false;
            }
            alpha_count += 1;
            if !in_word {
                word_count += 1;
                in_word = true;
            }
        } else if ch.is_ascii_digit() || ch.is_whitespace() || ch == '_' {
            if ch.is_whitespace() || ch == '_' {
                in_word = false;
            }
            continue;
        } else if matches!(ch, '/' | '-' | '&') {
            has_separator = true;
            in_word = false;
        } else {
            return false;
        }
    }

    if alpha_count < 4 || looks_like_solidity_statement(trimmed) {
        return false;
    }

    let context_supports_heading = prev
        .map(line_supports_section_heading_context)
        .unwrap_or(false)
        || next
            .map(line_supports_section_heading_context)
            .unwrap_or(false);

    has_separator || (word_count >= 2 && context_supports_heading) || context_supports_heading
}

fn looks_like_solidity_statement(trimmed: &str) -> bool {
    trimmed.contains(';')
        || trimmed.contains('(')
        || trimmed.contains(')')
        || trimmed.contains('=')
        || trimmed.contains('.')
        || trimmed.starts_with("0x")
        || trimmed.contains("**")
        || trimmed.contains("&&")
        || trimmed.contains("||")
        || trimmed.starts_with("contract ")
        || trimmed.starts_with("library ")
        || trimmed.starts_with("interface ")
        || trimmed.starts_with("function ")
        || trimmed.starts_with("modifier ")
        || trimmed.starts_with("event ")
        || trimmed.starts_with("error ")
        || trimmed.starts_with("struct ")
        || trimmed.starts_with("enum ")
        || trimmed.starts_with("type ")
        || trimmed.starts_with("using ")
        || trimmed.starts_with("return ")
        || trimmed.starts_with("if ")
        || trimmed.starts_with("for ")
        || trimmed.starts_with("while ")
        || trimmed.starts_with("revert ")
}

fn line_supports_section_heading_context(line: &str) -> bool {
    let trimmed = line.trim();
    trimmed.is_empty()
        || is_orphan_comment_line(trimmed)
        || is_decorative_comment_tail(trimmed)
        || trimmed.starts_with("///")
        || trimmed.starts_with("//")
        || trimmed.starts_with("function ")
        || trimmed.starts_with("modifier ")
        || trimmed.starts_with("event ")
        || trimmed.starts_with("error ")
        || trimmed.starts_with("struct ")
        || trimmed.starts_with("enum ")
        || trimmed.starts_with("contract ")
        || trimmed.starts_with("library ")
        || trimmed.starts_with("interface ")
}

fn previous_nonempty_line<'a>(lines: &'a [&str], idx: usize) -> Option<&'a str> {
    lines[..idx]
        .iter()
        .rev()
        .copied()
        .find(|line| !line.trim().is_empty())
}

fn next_nonempty_line<'a>(lines: &'a [&str], idx: usize) -> Option<&'a str> {
    lines
        .get(idx + 1..)
        .unwrap_or(&[])
        .iter()
        .copied()
        .find(|line| !line.trim().is_empty())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn drops_orphan_natspec_and_section_labels() {
        let input = r#"
type TokenId is uint256;
                            MOCKS
                            TESTS
 * @dev broken docs
 */
library Address {}
"#;

        let normalized = normalize_source(input);

        assert!(normalized.code.contains("type TokenId is uint256;"));
        assert!(normalized.code.contains("library Address {}"));
        assert!(!normalized.code.contains("MOCKS"));
        assert!(!normalized.code.contains("TESTS"));
        assert!(!normalized.code.contains("@dev broken docs"));
        assert!(normalized.report.has_changes());
    }

    #[test]
    fn keeps_minor_top_level_items_after_invalid_fragments() {
        let input = r#"
    if (utilization < 0) {
        return 0;
    }
type BalanceDelta is int256;
library BalanceDeltaLibrary {}
"#;

        let normalized = normalize_source(input);

        assert!(normalized.code.contains("type BalanceDelta is int256;"));
        assert!(normalized.code.contains("library BalanceDeltaLibrary {}"));
        assert!(!normalized.code.contains("utilization < 0"));
    }

    #[test]
    fn drops_generic_orphan_section_headings_and_decorative_tails() {
        let input = r#"
contract Example {
                          DEPOSIT/REDEEM LOGIC
                              OVERRIDES
                               QUERIES
                         LIQUIDATION FLOW
    //////////////////////////////////////////////////////////////*/
    function run() external {}
}
"#;

        let normalized = normalize_source(input);

        assert!(!normalized.code.contains("DEPOSIT/REDEEM LOGIC"));
        assert!(!normalized.code.contains("OVERRIDES"));
        assert!(!normalized.code.contains("QUERIES"));
        assert!(!normalized.code.contains("LIQUIDATION FLOW"));
        assert!(!normalized
            .code
            .contains("////////////////////////////////////////////////////////////*/"));
        assert!(normalized.code.contains("function run() external {}"));
    }

    #[test]
    fn does_not_drop_uppercase_constants_inside_code() {
        let input = r#"
contract Example {
    function run() external {
        _check(NO_BUFFER, COMPUTE_PREMIA_AS_COLLATERAL);
        uint256 LOCAL_CONSTANT = 1;
    }
}
"#;

        let normalized = normalize_source(input);

        assert!(normalized.code.contains("NO_BUFFER"));
        assert!(normalized.code.contains("COMPUTE_PREMIA_AS_COLLATERAL"));
        assert!(normalized.code.contains("LOCAL_CONSTANT"));
    }

    #[test]
    fn does_not_drop_unknown_uppercase_word_without_section_context() {
        let input = r#"
contract Example {
    string constant MODE = "OVERRIDE";
    bytes32 internal constant LIQUIDATION = bytes32(uint256(1));
}
"#;

        let normalized = normalize_source(input);

        assert!(normalized.code.contains("LIQUIDATION"));
    }

    #[test]
    fn drops_long_uppercase_section_heading() {
        let input = r#"
contract Example {
          LIFECYCLE OF A COLLATERAL TOKEN AND DELEGATE/REVOKE LOGIC

    function run() external {}
}
"#;

        let normalized = normalize_source(input);

        assert!(!normalized.code.contains("LIFECYCLE OF A COLLATERAL TOKEN"));
        assert!(normalized.code.contains("function run() external {}"));
    }

    #[test]
    fn drops_leaked_ascii_diagram_fragments_inside_functions() {
        let input = r#"
contract Example {
    function run() external {
        if (currentTick < tickLower) {
              L = lowerTick, U = upperTick
                    ▲            ◄──────────────^v───► (to MAX_TICK)
                    │
                    └─────▲─────┴────────┴────────► price tick
            value = lowerOut0 - upperOut0;
        }
    }
}
"#;

        let normalized = normalize_source(input);

        assert!(!normalized.code.contains("lowerTick, U = upperTick"));
        assert!(!normalized.code.contains("price tick"));
        assert!(normalized.code.contains("value = lowerOut0 - upperOut0;"));
    }

    #[test]
    fn drops_short_ascii_diagram_labels_near_art_context() {
        let input = r#"
contract Example {
    function run() external {
        if (currentTick >= tickUpper) {
                liquidity
                    ▲           upperOut0
                    │◄─^v─────────────────────►
                    └────────────────┴────────┴─▲─────► price tick
                                             L        U │
                                                      │
                                                   current
                                                    tick
            value = upperOut0 - lowerOut0;
        }
    }
}
"#;

        let normalized = normalize_source(input);

        assert!(!normalized.code.contains("liquidity"));
        assert!(!normalized.code.contains("price tick"));
        assert!(!normalized
            .code
            .contains("\n                                                   current"));
        assert!(!normalized
            .code
            .contains("\n                                                    tick"));
        assert!(normalized.code.contains("value = upperOut0 - lowerOut0;"));
    }

    #[test]
    fn drops_top_level_prose_that_starts_like_contract_definition() {
        let input = r#"
struct SwapParams {
    bool zeroForOne;
}

contract is only required for intermediate, library-like contracts.

library CustomRevert {
    function run() internal pure {}
}
"#;

        let normalized = normalize_source(input);

        assert!(!normalized
            .code
            .contains("contract is only required for intermediate"));
        assert!(normalized.code.contains("struct SwapParams"));
        assert!(normalized.code.contains("library CustomRevert"));
    }

    #[test]
    fn preserves_yul_let_assignments_that_look_like_prose() {
        let input = r#"
library CustomRevert {
    function bubbleUpAndRevertWith() internal pure {
        assembly ("memory-safe") {
            let encodedDataSize := mul(div(add(returndatasize(), 31), 32), 32)
            let mm := mulmod(a, b, not(0))
            mstore(add(fmp, 0x64), add(0xa0, encodedDataSize))
        }
    }
}
"#;

        let normalized = normalize_source(input);

        assert!(normalized.code.contains("let encodedDataSize :="));
        assert!(normalized.code.contains("let mm :="));
        assert!(normalized.code.contains("encodedDataSize"));
    }

    #[test]
    fn splits_top_level_chunks() {
        let input = r#"
contract A {}
library B {}
type C is uint256;
"#;

        let chunks = split_top_level_chunks(input);

        assert_eq!(chunks.len(), 3);
    }
}
