use std::path::{Path, PathBuf};

use tokio::process::Command;

use super::fallback::FallbackLevel;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CompileStatus {
    Success,
    Failed,
    ForgeUnavailable,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CompileErrorKind {
    Syntax,
    MissingSymbol,
    TypeError,
    MemberNotFound,
    InheritanceConflict,
    DuplicateDefinition,
    OverrideConflict,
    VisibilityError,
    Other,
}

#[derive(Debug, Clone)]
pub struct V2CompileError {
    pub kind: CompileErrorKind,
    pub message: String,
    pub line: Option<usize>,
    pub column: Option<usize>,
}

#[derive(Debug, Clone)]
pub struct CompileResult {
    pub status: CompileStatus,
    pub output: String,
    pub command: Option<String>,
    pub errors: Vec<V2CompileError>,
}

impl CompileResult {
    pub fn primary_error_kind(&self) -> Option<String> {
        self.errors
            .first()
            .map(|err| format!("{:?}", err.kind).to_ascii_lowercase())
            .or_else(|| {
                if self.status == CompileStatus::Failed {
                    Some("compile_failed".to_string())
                } else {
                    None
                }
            })
    }
}

#[derive(Debug, Clone)]
pub struct CompileScore {
    pub syntax_errors: usize,
    pub missing_symbol_errors: usize,
    pub member_not_found_errors: usize,
    pub type_errors: usize,
    pub inheritance_errors: usize,
    pub duplicate_definition_errors: usize,
    pub override_errors: usize,
    pub other_errors: usize,
    pub output_lines: usize,
}

impl CompileScore {
    pub fn weighted_total(&self) -> usize {
        self.syntax_errors * 10000
            + self.duplicate_definition_errors * 2000
            + self.inheritance_errors * 1500
            + self.override_errors * 1200
            + self.missing_symbol_errors * 500
            + self.member_not_found_errors * 400
            + self.type_errors * 200
            + self.other_errors
    }
}

pub struct CompileValidator {
    output_path: PathBuf,
    project_root: PathBuf,
    target_contract: String,
    target_test: String,
}

impl CompileValidator {
    pub fn new(
        output_path: PathBuf,
        project_root: PathBuf,
        target_contract: String,
        target_test: String,
    ) -> Self {
        Self {
            output_path,
            project_root,
            target_contract,
            target_test,
        }
    }

    pub async fn compile(&self, code: &str, level: FallbackLevel) -> CompileResult {
        if !self.is_forge_available() {
            return CompileResult {
                status: CompileStatus::ForgeUnavailable,
                output: "forge executable was not found".to_string(),
                command: None,
                errors: Vec::new(),
            };
        }
        let temp_project = match self.prepare_artifact_project(code, level) {
            Ok(path) => path,
            Err(e) => {
                return CompileResult {
                    status: CompileStatus::Failed,
                    output: e.clone(),
                    command: None,
                    errors: vec![V2CompileError {
                        kind: CompileErrorKind::Other,
                        message: e,
                        line: None,
                        column: None,
                    }],
                }
            }
        };
        let temp_target = temp_project.join("ResurrectedV2.t.sol");

        let command = if self.target_test.trim().is_empty() {
            vec![
                "forge".to_string(),
                "build".to_string(),
                "--root".to_string(),
                temp_project.to_string_lossy().to_string(),
                temp_target.to_string_lossy().to_string(),
                "--via-ir".to_string(),
            ]
        } else {
            vec![
                "forge".to_string(),
                "test".to_string(),
                "--root".to_string(),
                temp_project.to_string_lossy().to_string(),
                "--match-contract".to_string(),
                self.target_contract.clone(),
                "--match-test".to_string(),
                self.target_test.clone(),
                "--via-ir".to_string(),
            ]
        };
        let command_string = command.join(" ");

        let output = if self.target_test.trim().is_empty() {
            Command::new("forge")
                .arg("build")
                .arg("--root")
                .arg(&temp_project)
                .arg(&temp_target)
                .arg("--via-ir")
                .current_dir(&temp_project)
                .output()
                .await
        } else {
            Command::new("forge")
                .arg("test")
                .arg("--root")
                .arg(&temp_project)
                .arg("--match-contract")
                .arg(&self.target_contract)
                .arg("--match-test")
                .arg(&self.target_test)
                .arg("--via-ir")
                .current_dir(&temp_project)
                .output()
                .await
        };

        let output = match output {
            Ok(output) => output,
            Err(e) => {
                return CompileResult {
                    status: CompileStatus::Failed,
                    output: format!("failed to run forge: {}", e),
                    command: Some(command_string),
                    errors: vec![V2CompileError {
                        kind: CompileErrorKind::Other,
                        message: e.to_string(),
                        line: None,
                        column: None,
                    }],
                }
            }
        };
        let combined = format!(
            "{}{}",
            String::from_utf8_lossy(&output.stdout),
            String::from_utf8_lossy(&output.stderr)
        );
        let lower = combined.to_ascii_lowercase();
        let success = output.status.success()
            && !lower.contains("compiler run failed")
            && !lower.contains("error:")
            && !lower.contains("nothing to compile")
            && !lower.contains("no tests match")
            && !lower.contains("no tests found")
            && (lower.contains("compiler run successful")
                || lower.contains("suite result: ok")
                || lower.contains("test result: ok")
                || lower.contains("passed; 0 failed"));
        let errors = extract_errors(&combined, code);
        self.append_log(level, &command_string, success, &combined);
        CompileResult {
            status: if success {
                CompileStatus::Success
            } else {
                CompileStatus::Failed
            },
            output: combined,
            command: Some(command_string),
            errors,
        }
    }

    pub async fn check_original_project(&self) -> CompileResult {
        if !self.is_forge_available() {
            return CompileResult {
                status: CompileStatus::ForgeUnavailable,
                output: "forge executable was not found".to_string(),
                command: None,
                errors: Vec::new(),
            };
        }
        let mut command = Command::new("forge");
        command
            .arg("test")
            .arg("--root")
            .arg(&self.project_root)
            .arg("--via-ir");
        if !self.target_contract.trim().is_empty() {
            command.arg("--match-contract").arg(&self.target_contract);
        }
        if !self.target_test.trim().is_empty() {
            command.arg("--match-test").arg(&self.target_test);
        }
        command.current_dir(&self.project_root);
        let command_string = format!(
            "forge test --root {} --match-contract {} --match-test {} --via-ir",
            self.project_root.display(),
            self.target_contract,
            self.target_test
        );
        match command.output().await {
            Ok(output) => {
                let combined = format!(
                    "{}{}",
                    String::from_utf8_lossy(&output.stdout),
                    String::from_utf8_lossy(&output.stderr)
                );
                let success = output.status.success()
                    && !combined
                        .to_ascii_lowercase()
                        .contains("compiler run failed")
                    && !combined.to_ascii_lowercase().contains("error:")
                    && !combined.to_ascii_lowercase().contains("no tests match")
                    && !combined.to_ascii_lowercase().contains("no tests found");
                CompileResult {
                    status: if success {
                        CompileStatus::Success
                    } else {
                        CompileStatus::Failed
                    },
                    output: combined.clone(),
                    command: Some(command_string),
                    errors: extract_errors(&combined, ""),
                }
            }
            Err(e) => CompileResult {
                status: CompileStatus::Failed,
                output: e.to_string(),
                command: Some(command_string),
                errors: vec![V2CompileError {
                    kind: CompileErrorKind::Other,
                    message: e.to_string(),
                    line: None,
                    column: None,
                }],
            },
        }
    }

    fn is_forge_available(&self) -> bool {
        std::process::Command::new("forge")
            .arg("--version")
            .output()
            .is_ok()
    }

    fn append_log(&self, level: FallbackLevel, command: &str, success: bool, output: &str) {
        let mut log_path = self.output_path.clone();
        let stem = self
            .output_path
            .file_stem()
            .and_then(|stem| stem.to_str())
            .unwrap_or("resurrect_v2");
        log_path.set_file_name(format!("{}.v2.build.log", stem));
        if let Some(parent) = log_path.parent() {
            let _ = std::fs::create_dir_all(parent);
        }
        let record = format!(
            "\n=== resurrect_v2 level {} ({}) ===\ncommand: {}\nsuccess: {}\n{}\n",
            level.as_usize(),
            level.name(),
            command,
            success,
            output.trim_end()
        );
        let _ = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&log_path)
            .and_then(|mut file| {
                use std::io::Write;
                file.write_all(record.as_bytes())
            });
    }

    fn prepare_artifact_project(
        &self,
        code: &str,
        level: FallbackLevel,
    ) -> Result<PathBuf, String> {
        let project_dir = std::env::temp_dir().join(format!(
            "sc_slicer_v2_{}_{}",
            std::process::id(),
            level.as_usize()
        ));
        if project_dir.exists() {
            std::fs::remove_dir_all(&project_dir)
                .map_err(|e| format!("failed to reset temp forge project: {}", e))?;
        }
        std::fs::create_dir_all(&project_dir)
            .map_err(|e| format!("failed to create temp forge project: {}", e))?;
        let target = project_dir.join("ResurrectedV2.t.sol");
        std::fs::write(&target, code)
            .map_err(|e| format!("failed to write temp artifact {}: {}", target.display(), e))?;
        let foundry_toml = "[profile.default]\nsrc = \".\"\ntest = \".\"\nout = \"out\"\ncache_path = \"cache\"\nauto_detect_solc = true\nevm_version = \"cancun\"\noptimizer = true\noptimizer_runs = 200\nvia_ir = true\n";
        std::fs::write(project_dir.join("foundry.toml"), foundry_toml)
            .map_err(|e| format!("failed to write temp foundry.toml: {}", e))?;
        Ok(project_dir)
    }
}

fn extract_errors(output: &str, code: &str) -> Vec<V2CompileError> {
    let mut errors = Vec::new();
    let mut current_message: Option<String> = None;
    let mut current_line = None;
    let mut current_column = None;
    let mut current_snippet: Option<String> = None;
    let output_lines = code.lines().count();

    for line in output.lines() {
        let trimmed = line.trim();
        if let Some(rest) = trimmed.strip_prefix("Error: ") {
            if let Some(message) = current_message.take() {
                let line = current_line.take();
                let column = current_column.take();
                let message = enrich_message_with_code(message, line, column, code);
                errors.push(V2CompileError {
                    kind: classify_error(&message),
                    message,
                    line,
                    column,
                });
                current_snippet = None;
            }
            if rest != "Compiler run failed:" {
                current_message = Some(rest.to_string());
            }
        } else if let Some(rest) = trimmed.strip_prefix("Error (") {
            if let Some((_, message)) = rest.split_once("): ") {
                if let Some(prev) = current_message.take() {
                    let line = current_line.take();
                    let column = current_column.take();
                    let prev = enrich_message_with_code(prev, line, column, code);
                    errors.push(V2CompileError {
                        kind: classify_error(&prev),
                        message: prev,
                        line,
                        column,
                    });
                    current_snippet = None;
                }
                current_message = Some(message.to_string());
            }
        } else if let Some((line_no, col)) = parse_location(trimmed) {
            current_line = Some(line_no);
            current_column = Some(col);
        } else if let Some(snippet) = parse_source_snippet(trimmed) {
            current_snippet = Some(snippet);
        } else if trimmed.starts_with('|') && trimmed.contains('^') {
            if let (Some(message), Some(snippet)) = (&mut current_message, &current_snippet) {
                message.push('\n');
                message.push_str(snippet);
                message.push('\n');
                message.push_str(trimmed);
            }
        }
    }

    if let Some(message) = current_message.take() {
        let message = enrich_message_with_code(message, current_line, current_column, code);
        errors.push(V2CompileError {
            kind: classify_error(&message),
            message,
            line: current_line,
            column: current_column,
        });
    }

    if errors.is_empty()
        && !output.trim().is_empty()
        && output.to_ascii_lowercase().contains("error")
    {
        errors.push(V2CompileError {
            kind: CompileErrorKind::Other,
            message: output.to_string(),
            line: None,
            column: None,
        });
    }

    let _score = CompileScore {
        syntax_errors: errors
            .iter()
            .filter(|e| e.kind == CompileErrorKind::Syntax)
            .count(),
        missing_symbol_errors: errors
            .iter()
            .filter(|e| e.kind == CompileErrorKind::MissingSymbol)
            .count(),
        member_not_found_errors: errors
            .iter()
            .filter(|e| e.kind == CompileErrorKind::MemberNotFound)
            .count(),
        type_errors: errors
            .iter()
            .filter(|e| e.kind == CompileErrorKind::TypeError)
            .count(),
        inheritance_errors: errors
            .iter()
            .filter(|e| e.kind == CompileErrorKind::InheritanceConflict)
            .count(),
        duplicate_definition_errors: errors
            .iter()
            .filter(|e| e.kind == CompileErrorKind::DuplicateDefinition)
            .count(),
        override_errors: errors
            .iter()
            .filter(|e| e.kind == CompileErrorKind::OverrideConflict)
            .count(),
        other_errors: errors
            .iter()
            .filter(|e| e.kind == CompileErrorKind::Other)
            .count(),
        output_lines,
    };

    errors
}

fn classify_error(message: &str) -> CompileErrorKind {
    let lower = message.to_ascii_lowercase();
    if lower.contains("expected")
        || lower.contains("unexpected")
        || lower.contains("parsererror")
        || lower.contains("syntax")
    {
        CompileErrorKind::Syntax
    } else if lower.contains("undeclared identifier")
        || lower.contains("identifier not found")
        || lower.contains("not found or not unique")
        || lower.contains("not a library name")
    {
        CompileErrorKind::MissingSymbol
    } else if lower.contains("member") && lower.contains("not found") {
        CompileErrorKind::MemberNotFound
    } else if lower.contains("already declared") || lower.contains("identifier already declared") {
        CompileErrorKind::DuplicateDefinition
    } else if lower.contains("override") {
        CompileErrorKind::OverrideConflict
    } else if lower.contains("inheritance") || lower.contains("linearization") {
        CompileErrorKind::InheritanceConflict
    } else if lower.contains("visibility") {
        CompileErrorKind::VisibilityError
    } else if lower.contains("typeerror") || lower.contains("type ") {
        CompileErrorKind::TypeError
    } else {
        CompileErrorKind::Other
    }
}

fn parse_location(line: &str) -> Option<(usize, usize)> {
    let rest = line.strip_prefix("--> ")?;
    let rest = rest.strip_suffix(':').unwrap_or(rest);
    let mut parts = rest.rsplitn(3, ':');
    let column = parts.next()?.parse().ok()?;
    let line_no = parts.next()?.parse().ok()?;
    Some((line_no, column))
}

fn parse_source_snippet(line: &str) -> Option<String> {
    let (line_no, rest) = line.split_once('|')?;
    if line_no.trim().chars().all(|ch| ch.is_ascii_digit()) {
        Some(rest.strip_prefix(' ').unwrap_or(rest).to_string())
    } else {
        None
    }
}

fn enrich_message_with_code(
    mut message: String,
    line: Option<usize>,
    column: Option<usize>,
    code: &str,
) -> String {
    if message.lines().count() > 1 {
        return message;
    }
    let Some(line_no) = line else {
        return message;
    };
    let Some(source_line) = code.lines().nth(line_no.saturating_sub(1)) else {
        return message;
    };
    message.push('\n');
    message.push_str(source_line);
    if let Some(column) = column {
        message.push('\n');
        message.push_str("| ");
        message.push_str(&" ".repeat(column.saturating_sub(1)));
        message.push('^');
    }
    message
}

fn exact_identifier_regex(identifier: &str) -> String {
    let escaped = identifier
        .chars()
        .flat_map(|ch| match ch {
            '\\' | '^' | '$' | '.' | '|' | '?' | '*' | '+' | '(' | ')' | '[' | ']' | '{' | '}' => {
                vec!['\\', ch]
            }
            _ => vec![ch],
        })
        .collect::<String>();
    format!("^{}$", escaped)
}
