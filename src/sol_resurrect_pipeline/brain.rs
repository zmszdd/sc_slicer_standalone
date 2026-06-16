#![allow(unused)]
use serde_json::Value;
use std::collections::HashMap;

use crate::sol_resurrect_pipeline::extractor;

#[derive(Debug, Clone)]
pub struct RepairGuidance {
    pub target_contract: String,
    pub entry_function: String,
    pub focus_symbol: String,
    pub poc_dependencies: Option<String>,
    pub max_error_count: usize,
    pub max_context_chars: usize,
    pub max_append_definitions: usize,
}

impl RepairGuidance {
    pub fn new(target_contract: String, entry_function: String, focus_symbol: String) -> Self {
        Self {
            target_contract,
            entry_function,
            focus_symbol,
            poc_dependencies: None,
            max_error_count: 8,
            max_context_chars: 16_000,
            max_append_definitions: 6,
        }
    }

    pub fn with_poc_dependencies(mut self, deps: impl Into<String>) -> Self {
        let deps = deps.into().trim().to_string();
        if !deps.is_empty() {
            self.poc_dependencies = Some(deps);
        }
        self
    }
}

#[derive(Debug)]
pub struct InferenceResult {
    pub mock_libraries: HashMap<String, String>,
    pub rehoming_map: HashMap<String, String>,
}

pub struct ContextBrain {
    solidity_rules: String,
}

impl ContextBrain {
    pub fn new(_api_key: String, _base_url: String, _model: String) -> Self {
        let solidity_rules = "[Solidity Generation Rules]\n\
            1. Definition Completeness:\n\
               - If code references a nested struct (Contract.Struct), define that struct inside the contract.\n\
               - If code uses 'revert CustomError()', declare 'error CustomError();' within the contract.\n\
            2. Scope Management:\n\
               - Do not leave orphan types. Every type in signatures must be defined.\n\
            3. Shadowing Prevention:\n\
               - If a function argument would shadow a state variable with the same name, prefix the argument with an underscore.\n"
            .to_string();

        Self { solidity_rules }
    }

    pub async fn deduce_minimal_goals(
        &self,
        code: &str,
        target_contract: &str,
        entry_function: &str,
    ) -> Result<String, Box<dyn std::error::Error>> {
        let _ = (code, target_contract, entry_function);
        Ok("Required: []\nNon-goals:\n  - LLM dependency deduction disabled".to_string())
    }

    pub async fn infer(
        &self,
        code: &str,
        original_source: &str,
        _guidance: Option<&RepairGuidance>,
        ast_extraction: Option<crate::sol_resurrect_pipeline::ast_extractor::ExtractionResult>,
    ) -> Result<InferenceResult, Box<dyn std::error::Error>> {
        println!("      [Brain] Starting AST-based inference pipeline...");
        let mut result = InferenceResult {
            mock_libraries: HashMap::new(),
            rehoming_map: HashMap::new(),
        };

        // Extract missing types using AST
        if let Some(ast_ext) = ast_extraction {
            println!("      [Brain] Using pre-computed AST extraction results.");

            let _missing_interfaces: Vec<String> = Vec::new();
            let mut missing_mocks = Vec::new();

            for restore in ast_ext.restores {
                match restore {
                    crate::sol_resurrect_pipeline::ast_extractor::RestoreAction::SourceBacked(def) => {
                        if let Some(src) = def.source_text {
                            println!("      [Brain] SourceBacked restore for {}", def.name);
                            result.mock_libraries.insert(format!("_SourceBacked_{}", def.name), src);
                        } else {
                            if let Some(source_code) = self.extract_definition_from_source(original_source, &def.name) {
                                println!("      [Brain] Fallback string-extract for {}", def.name);
                                result.mock_libraries.insert(format!("_SourceBacked_{}", def.name), source_code);
                            } else {
                                println!("      [Brain] WARNING: Could not find source for SourceBacked {}", def.name);
                            }
                        }
                    }
                    crate::sol_resurrect_pipeline::ast_extractor::RestoreAction::ExternalMock(req) => {
                        if let Some(source_code) = self.extract_definition_from_source(original_source, &req.name) {
                            println!("      [Brain] SourceBacked boundary restore for {}", req.name);
                            result
                                .mock_libraries
                                .insert(format!("_SourceBacked_{}", req.name), source_code);
                        } else {
                            missing_mocks.push(req.name);
                        }
                    }
                    crate::sol_resurrect_pipeline::ast_extractor::RestoreAction::SkipAlreadyPresent(id) => {
                        println!("      [Brain] Skipping already present definition: {:?}", id);
                    }
                    crate::sol_resurrect_pipeline::ast_extractor::RestoreAction::Unresolved(diag) => {
                        println!("      [Brain] WARNING: Unresolved definition: {}", diag.message);
                    }
                }
            }

            if !missing_mocks.is_empty() {
                println!(
                    "      [Brain] AST detected external boundaries for deterministic stubs: {:?}",
                    missing_mocks
                );
                for (i, chunk) in missing_mocks.chunks(8).enumerate() {
                    result.mock_libraries.insert(
                        format!("_DeterministicMockBatch_{}", i),
                        self.generate_empty_contracts(chunk),
                    );
                }
            }
        } else {
            let extraction = match extractor::parse_and_extract(code) {
                Ok(ext) => ext,
                Err(e) => {
                    println!(
                        "      [Brain] AST Extraction failed: {}. Falling back to empty results.",
                        e
                    );
                    extractor::ExtractionResult::default()
                }
            };

            // Helper closure to process a list of missing names
            let process_missing = |names: Vec<String>,
                                   category: &str,
                                   mocks: &mut std::collections::HashMap<String, String>|
             -> Vec<String> {
                let mut remaining = Vec::new();
                for name in names {
                    if let Some(source_code) =
                        self.extract_definition_from_source(original_source, &name)
                    {
                        println!(
                            "      [Brain] Extracted {} {} from original source",
                            category, name
                        );
                        mocks.insert(format!("_Original_{}", name), source_code);
                    } else {
                        remaining.push(name);
                    }
                }
                remaining
            };

            // 1. Missing Interfaces
            let mut missing_interfaces = extraction.missing_interfaces;
            if !missing_interfaces.is_empty() {
                missing_interfaces =
                    process_missing(missing_interfaces, "interface", &mut result.mock_libraries);
                if !missing_interfaces.is_empty() {
                    println!(
                        "      [Brain] AST detected missing interfaces for deterministic stubs: {:?}",
                        missing_interfaces
                    );
                    for (i, chunk) in missing_interfaces.chunks(12).enumerate() {
                        result.mock_libraries.insert(
                            format!("_InterfaceBatch_{}", i),
                            self.generate_empty_interfaces(chunk),
                        );
                    }
                }
            }

            // 2. Missing Mocks
            let mut missing_mocks = extraction.missing_mocks;
            if !missing_mocks.is_empty() {
                missing_mocks = process_missing(missing_mocks, "mock", &mut result.mock_libraries);
                if !missing_mocks.is_empty() {
                    println!(
                        "      [Brain] AST detected missing mocks for deterministic stubs: {:?}",
                        missing_mocks
                    );
                    for (i, chunk) in missing_mocks.chunks(8).enumerate() {
                        result.mock_libraries.insert(
                            format!("_MockBatch_{}", i),
                            self.generate_empty_contracts(chunk),
                        );
                    }
                }
            }

            // 3. Missing Errors
            let mut missing_errors = extraction.missing_errors;
            if !missing_errors.is_empty() {
                missing_errors =
                    process_missing(missing_errors, "error", &mut result.mock_libraries);
                if !missing_errors.is_empty() {
                    println!(
                        "      [Brain] AST Detected missing errors for LLM: {:?}",
                        missing_errors
                    );
                    let error_code = self.generate_error_definitions(&missing_errors);
                    result
                        .mock_libraries
                        .insert("_ErrorDefinitions".to_string(), error_code);
                }
            }
        }

        Ok(result)
    }

    fn extract_definition_from_source(&self, source: &str, name: &str) -> Option<String> {
        let lines: Vec<&str> = source.lines().collect();

        let has_declaration = |line: &str, decl_type: &str, name: &str| -> bool {
            let pattern1 = format!("{} {} ", decl_type, name);
            let pattern2 = format!("{} {}{{", decl_type, name);
            let pattern3 = format!("{} {}(", decl_type, name);
            let pattern4 = format!("{} {};", decl_type, name);
            line.contains(&pattern1)
                || line.contains(&pattern2)
                || line.contains(&pattern3)
                || line.contains(&pattern4)
        };

        for i in 0..lines.len() {
            let line = lines[i].trim();
            if line.starts_with("//") || line.starts_with('*') {
                continue;
            }

            if has_declaration(line, "contract", name)
                || has_declaration(line, "abstract contract", name)
                || has_declaration(line, "interface", name)
                || has_declaration(line, "library", name)
            {
                return extract_block_from_lines(&lines, i);
            }

            if has_declaration(line, "struct", name)
                || has_declaration(line, "enum", name)
                || has_declaration(line, "error", name)
                || has_declaration(line, "type", name)
            {
                let mut type_lines = Vec::new();
                let mut brace_count: i32 = 0;
                let mut j = i;
                let mut signature_complete = false;
                let mut signature_lines = Vec::new();

                while j < lines.len() && !signature_complete {
                    let current_line = lines[j];
                    signature_lines.push(current_line.to_string());

                    if current_line.contains('{') || current_line.trim().ends_with(';') {
                        signature_complete = true;
                    }

                    brace_count += current_line.chars().filter(|&c| c == '{').count() as i32;
                    let close_count = current_line.chars().filter(|&c| c == '}').count() as i32;
                    if brace_count >= close_count {
                        brace_count -= close_count;
                    } else {
                        brace_count = 0;
                    }
                    j += 1;
                }

                let signature = signature_lines.join("\n");
                type_lines.push(signature.clone());

                if signature.trim().ends_with(';') {
                    return Some(signature);
                }

                while j < lines.len() && brace_count > 0 {
                    let current_line = lines[j];
                    type_lines.push(current_line.to_string());

                    brace_count += current_line.chars().filter(|&c| c == '{').count() as i32;
                    let close_count = current_line.chars().filter(|&c| c == '}').count() as i32;
                    if brace_count >= close_count {
                        brace_count -= close_count;
                    } else {
                        brace_count = 0;
                    }
                    j += 1;
                }

                return Some(type_lines.join("\n"));
            }
        }
        None
    }

    fn generate_error_definitions(&self, error_names: &[String]) -> String {
        let mut lines = vec!["// Auto-generated error definitions".to_string()];
        let mut sorted = error_names.to_vec();
        sorted.sort();
        for e in sorted {
            lines.push(format!("error {}();", e));
        }
        lines.join("\n")
    }

    fn generate_empty_interfaces(&self, names: &[String]) -> String {
        names
            .iter()
            .map(|name| format!("interface {} {{}}", name))
            .collect::<Vec<_>>()
            .join("\n\n")
    }

    fn generate_empty_contracts(&self, names: &[String]) -> String {
        names
            .iter()
            .map(|name| format!("contract {} {{}}", name))
            .collect::<Vec<_>>()
            .join("\n\n")
    }

    pub async fn generate_repair_plan(
        &self,
        code: &str,
        errors: &[String],
        guidance: Option<&RepairGuidance>,
    ) -> Result<Value, Box<dyn std::error::Error>> {
        let _ = (code, errors, guidance);
        Ok(serde_json::json!({
            "append_definitions": [],
            "replace_definition": [],
            "insert_members": [],
            "remove_lines": [],
            "replace_function": [],
            "code_to_append": ""
        }))
    }
}

fn extract_block_from_lines(lines: &[&str], start: usize) -> Option<String> {
    let mut out = Vec::new();
    let mut brace_count = 0i32;
    let mut seen_open = false;

    for line in lines.iter().skip(start) {
        out.push((*line).to_string());
        let opens = line.chars().filter(|&c| c == '{').count() as i32;
        let closes = line.chars().filter(|&c| c == '}').count() as i32;
        if opens > 0 {
            seen_open = true;
        }
        brace_count += opens - closes;
        if seen_open && brace_count <= 0 {
            return Some(out.join("\n"));
        }
        if !seen_open && line.trim_end().ends_with(';') {
            return Some(out.join("\n"));
        }
    }

    None
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_guidance_builder_empty() {
        let rg = RepairGuidance::new("A".to_string(), "B".to_string(), "C".to_string());
        assert_eq!(rg.poc_dependencies, None);

        let rg2 = rg.clone().with_poc_dependencies("");
        assert_eq!(rg2.poc_dependencies, None);

        let rg3 = rg.clone().with_poc_dependencies("   \n  ");
        assert_eq!(rg3.poc_dependencies, None);

        let rg4 = rg.with_poc_dependencies("valid_deps");
        assert_eq!(rg4.poc_dependencies, Some("valid_deps".to_string()));
    }
}
