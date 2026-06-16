use super::brain::InferenceResult;
use super::normalizer;
use serde_json::Value;
use std::collections::HashSet;

pub struct Assembler;

impl Assembler {
    pub fn new() -> Self {
        Self
    }

    pub fn assemble(&self, base_code: &str, inference_result: &InferenceResult) -> String {
        let mut assembled = normalizer::normalize_solidity_fragment(base_code);
        let mut known_defs = normalizer::top_level_definition_names(&assembled);
        let mut batches: Vec<_> = inference_result.mock_libraries.iter().collect();
        batches.sort_by(|a, b| a.0.cmp(b.0));

        let mut to_inject = String::new();
        for (name, code) in batches {
            let fragment = normalizer::SourceNormalizer::for_llm_fragment()
                .normalize(code)
                .code;
            if name.starts_with("_Original_") {
                let replacement_defs = normalizer::top_level_definition_names(&fragment);
                if !replacement_defs.is_empty() {
                    assembled = remove_top_level_definitions(&assembled, &replacement_defs);
                    known_defs = normalizer::top_level_definition_names(&assembled);
                }
            }
            let filtered = self.filter_duplicate_chunks(&fragment, &mut known_defs);
            if filtered.trim().is_empty() {
                continue;
            }

            to_inject.push_str(&format!("\n\n// Mock for {}\n{}\n", name, filtered));
        }

        assembled = insert_after_pragmas_and_imports(&assembled, &to_inject);

        normalizer::normalize_solidity_fragment(&assembled)
    }

    pub fn apply_repair_plan(&self, code: &str, plan: &Value) -> String {
        println!("APPLY REPAIR PLAN CALLED: {plan:?}");
        let mut assembled = code.to_string();

        if let Some(items) = plan.get("remove_lines").and_then(|v| v.as_array()) {
            assembled = apply_remove_lines(&assembled, items);
        }

        if let Some(items) = plan.get("replace_definition").and_then(|v| v.as_array()) {
            for item in items {
                let Some(name) = item.get("name").and_then(|v| v.as_str()) else {
                    continue;
                };
                let Some(replacement) = item.get("code").and_then(|v| v.as_str()) else {
                    continue;
                };
                if replacement.trim().is_empty() {
                    continue;
                }
                assembled = replace_top_level_definition(&assembled, name, replacement);
            }
        }

        if let Some(items) = plan.get("replace_function").and_then(|v| v.as_array()) {
            for item in items {
                let Some(name) = item.get("name").and_then(|v| v.as_str()) else {
                    continue;
                };
                let container = item.get("container").and_then(|v| v.as_str());
                let param_count = item
                    .get("param_count")
                    .and_then(|v| v.as_u64())
                    .map(|v| v as usize);
                let Some(replacement) = item.get("code").and_then(|v| v.as_str()) else {
                    continue;
                };
                if replacement.trim().is_empty() {
                    continue;
                }
                assembled = replace_function(&assembled, container, name, param_count, replacement);
            }
        }

        if let Some(items) = plan.get("insert_members").and_then(|v| v.as_array()) {
            for item in items {
                let Some(container) = item.get("container").and_then(|v| v.as_str()) else {
                    continue;
                };
                let Some(members) = item.get("code").and_then(|v| v.as_str()) else {
                    continue;
                };
                if members.trim().is_empty() {
                    continue;
                }
                assembled = insert_members_into_container(&assembled, container, members);
            }
        }

        let mut append_parts = Vec::new();
        if let Some(items) = plan.get("append_definitions").and_then(|v| v.as_array()) {
            for item in items {
                if let Some(code) = item.as_str() {
                    append_parts.push(code.to_string());
                }
            }
        }
        if let Some(append_code) = plan.get("code_to_append").and_then(|v| v.as_str()) {
            append_parts.push(append_code.to_string());
        }
        let append_code = append_parts.join("\n\n");
        if !append_code.trim().is_empty() {
            let append_code = normalizer::SourceNormalizer::for_llm_fragment()
                .normalize(&append_code)
                .code;
            let mut append_defs = HashSet::new();
            let append_code = self.filter_duplicate_chunks(&append_code, &mut append_defs);
            let new_defs = normalizer::top_level_definition_names(&append_code);
            if !new_defs.is_empty() {
                let mut kept_chunks = Vec::new();
                for chunk in normalizer::split_top_level_chunks(&assembled) {
                    let chunk_defs = normalizer::top_level_definition_names(&chunk);
                    if chunk_defs.is_disjoint(&new_defs) {
                        kept_chunks.push(chunk);
                    }
                }
                assembled = kept_chunks.join("\n\n");
                let to_inject = format!("\n\n// Auto-repair appended code\n{}", append_code);
                assembled = insert_after_pragmas_and_imports(&assembled, &to_inject);
            }
        }
        normalizer::normalize_solidity_fragment(&assembled)
    }

    fn filter_duplicate_chunks(&self, code: &str, known_defs: &mut HashSet<String>) -> String {
        let mut kept = Vec::new();

        for chunk in normalizer::split_top_level_chunks(code) {
            let names = normalizer::top_level_definition_names(&chunk);
            if names.is_empty() {
                if normalizer::looks_parse_worthy(&chunk) {
                    kept.push(chunk);
                }
                continue;
            }

            if names.iter().any(|name| known_defs.contains(name)) {
                continue;
            }

            for name in names {
                known_defs.insert(name);
            }
            kept.push(chunk);
        }

        kept.join("\n\n")
    }
}

fn remove_top_level_definitions(code: &str, definitions: &HashSet<String>) -> String {
    normalizer::split_top_level_chunks(code)
        .into_iter()
        .filter(|chunk| {
            let chunk_defs = normalizer::top_level_definition_names(chunk);
            chunk_defs.is_empty() || chunk_defs.is_disjoint(definitions)
        })
        .collect::<Vec<_>>()
        .join("\n\n")
}

fn replace_top_level_definition(code: &str, name: &str, replacement: &str) -> String {
    let replacement = normalizer::SourceNormalizer::for_llm_fragment()
        .normalize(replacement)
        .code;
    let mut replaced = false;
    let chunks = normalizer::split_top_level_chunks(code)
        .into_iter()
        .map(|chunk| {
            if normalizer::top_level_definition_names(&chunk).contains(name) {
                replaced = true;
                replacement.clone()
            } else {
                chunk
            }
        })
        .collect::<Vec<_>>();
    if replaced {
        chunks.join("\n\n")
    } else {
        format!("{}\n\n{}", replacement, code)
    }
}

fn replace_function(
    code: &str,
    container: Option<&str>,
    name: &str,
    param_count: Option<usize>,
    replacement: &str,
) -> String {
    let lines: Vec<&str> = code.lines().collect();
    let replacement = normalizer::SourceNormalizer::for_llm_fragment()
        .normalize(replacement)
        .code;
    for (idx, line) in lines.iter().enumerate() {
        let trimmed = line.trim_start();
        if !trimmed.starts_with("function ")
            || parse_function_name(trimmed).as_deref() != Some(name)
        {
            continue;
        }
        let current_container = find_enclosing_container_start(&lines, idx + 1)
            .and_then(|container_idx| parse_container_name(lines[container_idx].trim_start()));
        if container.is_some() && current_container.as_deref() != container {
            continue;
        }
        if param_count.is_some() && function_param_count_from_lines(&lines, idx) != param_count {
            continue;
        }
        let Some(end) = find_block_end(&lines, idx) else {
            continue;
        };
        let mut out = Vec::new();
        for line in lines.iter().take(idx) {
            out.push((*line).to_string());
        }
        out.push(replacement);
        for line in lines.iter().skip(end + 1) {
            out.push((*line).to_string());
        }
        return out.join("\n");
    }
    code.to_string()
}

fn insert_members_into_container(code: &str, container: &str, members: &str) -> String {
    let lines: Vec<&str> = code.lines().collect();
    for (idx, line) in lines.iter().enumerate() {
        if parse_container_name(line.trim_start()).as_deref() != Some(container) {
            continue;
        }
        let Some(end) = find_block_end(&lines, idx) else {
            continue;
        };
        let indent = "    ";
        let member_block = members
            .lines()
            .map(|line| {
                if line.trim().is_empty() {
                    String::new()
                } else {
                    format!("{}{}", indent, line.trim())
                }
            })
            .collect::<Vec<_>>()
            .join("\n");
        let mut out = Vec::new();
        for line in lines.iter().take(end) {
            out.push((*line).to_string());
        }
        out.push(member_block);
        for line in lines.iter().skip(end) {
            out.push((*line).to_string());
        }
        return out.join("\n");
    }
    code.to_string()
}

fn apply_remove_lines(code: &str, items: &[Value]) -> String {
    let mut remove = HashSet::new();
    for item in items {
        let Some(start) = item
            .get("start")
            .and_then(|v| v.as_u64())
            .map(|v| v as usize)
        else {
            continue;
        };
        let end = item
            .get("end")
            .and_then(|v| v.as_u64())
            .map(|v| v as usize)
            .unwrap_or(start);
        for line_no in start..=end {
            remove.insert(line_no);
        }
    }
    code.lines()
        .enumerate()
        .filter_map(|(idx, line)| (!remove.contains(&(idx + 1))).then_some(line))
        .collect::<Vec<_>>()
        .join("\n")
}

fn insert_after_pragmas_and_imports(code: &str, to_inject: &str) -> String {
    let mut lines: Vec<&str> = code.lines().collect();
    let mut insert_idx = 0;

    for (i, line) in lines.iter().enumerate() {
        let trimmed = line.trim();
        if trimmed.starts_with("pragma ") || trimmed.starts_with("import ") {
            insert_idx = i + 1;
        }
    }

    lines.insert(insert_idx, to_inject);
    lines.join("\n")
}

fn parse_container_name(line: &str) -> Option<String> {
    let rest = line
        .strip_prefix("abstract contract ")
        .or_else(|| line.strip_prefix("contract "))
        .or_else(|| line.strip_prefix("interface "))
        .or_else(|| line.strip_prefix("library "))?;
    let name = rest
        .split(|ch: char| ch.is_whitespace() || ch == '{')
        .next()
        .unwrap_or("");
    (!name.is_empty()).then(|| name.to_string())
}

fn parse_function_name(line: &str) -> Option<String> {
    let rest = line.trim_start().strip_prefix("function ")?;
    let name = rest
        .split(|ch: char| ch == '(' || ch.is_whitespace())
        .next()
        .unwrap_or("");
    (!name.is_empty()).then(|| name.to_string())
}

fn find_enclosing_container_start(lines: &[&str], line_no: usize) -> Option<usize> {
    let start = line_no.saturating_sub(1).min(lines.len().saturating_sub(1));
    for idx in (0..=start).rev() {
        if parse_container_name(lines[idx].trim_start()).is_some() {
            return Some(idx);
        }
    }
    None
}

fn find_block_end(lines: &[&str], start: usize) -> Option<usize> {
    let mut depth = 0i32;
    let mut seen_body = false;
    let mut in_block_comment = false;
    for (idx, line) in lines.iter().enumerate().skip(start) {
        let mut in_single_quote = false;
        let mut in_double_quote = false;
        let mut chars = line.chars().peekable();
        while let Some(ch) = chars.next() {
            if in_block_comment {
                if ch == '*' && chars.peek() == Some(&'/') {
                    chars.next();
                    in_block_comment = false;
                }
                continue;
            }
            if in_single_quote {
                if ch == '\\' {
                    chars.next();
                } else if ch == '\'' {
                    in_single_quote = false;
                }
                continue;
            }
            if in_double_quote {
                if ch == '\\' {
                    chars.next();
                } else if ch == '"' {
                    in_double_quote = false;
                }
                continue;
            }
            match ch {
                '/' if chars.peek() == Some(&'/') => break,
                '/' if chars.peek() == Some(&'*') => {
                    chars.next();
                    in_block_comment = true;
                }
                '\'' => in_single_quote = true,
                '"' => in_double_quote = true,
                '{' => {
                    depth += 1;
                    seen_body = true;
                }
                '}' => {
                    depth -= 1;
                    if depth <= 0 && seen_body {
                        return Some(idx);
                    }
                }
                _ => {}
            }
        }
        if !seen_body && line.trim_end().ends_with(';') {
            return Some(idx);
        }
    }
    None
}

fn function_param_count_from_lines(lines: &[&str], start: usize) -> Option<usize> {
    let mut header = String::new();
    for line in lines.iter().skip(start).take(40) {
        header.push(' ');
        header.push_str(line.trim());
        if line.contains('{') || line.trim_end().ends_with(';') {
            break;
        }
    }
    count_function_params(&header)
}

fn count_function_params(header: &str) -> Option<usize> {
    let open = header.find('(')?;
    let mut depth = 0i32;
    let mut params = String::new();
    let mut started = false;
    for ch in header[open..].chars() {
        if ch == '(' {
            depth += 1;
            if !started {
                started = true;
                continue;
            }
        } else if ch == ')' {
            depth -= 1;
            if depth == 0 {
                break;
            }
        }
        if started {
            params.push(ch);
        }
    }
    let params = params.trim();
    if params.is_empty() {
        return Some(0);
    }
    let mut count = 1usize;
    let mut nested = 0i32;
    for ch in params.chars() {
        match ch {
            '(' | '[' => nested += 1,
            ')' | ']' => nested -= 1,
            ',' if nested == 0 => count += 1,
            _ => {}
        }
    }
    Some(count)
}
