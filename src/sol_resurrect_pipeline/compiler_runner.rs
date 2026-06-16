use std::io::Write;
use std::path::{Path, PathBuf};
use tokio::process::Command;

#[derive(Debug, Clone)]
pub struct HarnessValidationTarget {
    pub match_contract: String,
    pub match_test: String,
}

impl HarnessValidationTarget {
    pub fn new(match_contract: String, match_test: String) -> Self {
        Self {
            match_contract,
            match_test,
        }
    }

    fn is_active(&self) -> bool {
        !self.match_contract.trim().is_empty() && !self.match_test.trim().is_empty()
    }

    fn exact_contract_regex(&self) -> String {
        exact_solidity_identifier_regex(&self.match_contract)
    }

    fn exact_test_regex(&self) -> String {
        exact_solidity_identifier_regex(&self.match_test)
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CompilerErrorCategory {
    Syntax,
    Declaration,
    Type,
    Duplicate,
    MissingSymbol,
    Other,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CompileScore {
    pub syntax: usize,
    pub declaration: usize,
    pub type_error: usize,
    pub duplicate: usize,
    pub missing_symbol: usize,
    pub other: usize,
    pub total: usize,
    pub code_size: usize,
}

impl CompileScore {
    pub fn new(errors: &[CompilerError], code_lines: usize) -> Self {
        let mut score = Self {
            syntax: 0,
            declaration: 0,
            type_error: 0,
            duplicate: 0,
            missing_symbol: 0,
            other: 0,
            total: errors.len(),
            code_size: code_lines,
        };
        for err in errors {
            match err.category {
                CompilerErrorCategory::Syntax => score.syntax += 1,
                CompilerErrorCategory::Declaration => score.declaration += 1,
                CompilerErrorCategory::Type => score.type_error += 1,
                CompilerErrorCategory::Duplicate => score.duplicate += 1,
                CompilerErrorCategory::MissingSymbol => score.missing_symbol += 1,
                CompilerErrorCategory::Other => score.other += 1,
            }
        }
        score
    }

    pub fn weighted_total(&self) -> usize {
        self.syntax * 10000
            + self.declaration * 1000
            + self.duplicate * 500
            + self.missing_symbol * 100
            + self.type_error * 10
            + self.other
    }
}

pub fn should_accept_patch(old: &CompileScore, new: &CompileScore, same_fingerprint: bool) -> bool {
    // 1. If errors are identical conceptually, we shouldn't accept just because code size inflated.
    if same_fingerprint {
        return false;
    }

    let old_wt = old.weighted_total();
    let new_wt = new.weighted_total();

    // 2. Strict monotonic requirement: weighted total must decrease,
    // OR stay the same but total errors strictly decrease (meaning less 'other' or equal mix but fewer).
    let monotonic_improvement = new_wt < old_wt || (new_wt == old_wt && new.total < old.total);

    if !monotonic_improvement {
        return false;
    }

    // 3. Safety check against runaway code expansion (hallucinations).
    // If the patch expands code by >20% and at least 20 lines without fixing everything, reject it.
    if new.total > 0
        && new.code_size > old.code_size + 20
        && new.code_size as f64 > (old.code_size as f64 * 1.2)
    {
        return false;
    }

    true
}

#[derive(Debug, Clone)]
pub struct CompilerError {
    pub code: Option<String>,
    pub message: String,
    pub file: Option<PathBuf>,
    pub line: Option<usize>,
    pub column: Option<usize>,
    pub category: CompilerErrorCategory,
    pub snippet: Vec<String>,
}

pub struct CompilerRunner {
    output_path: PathBuf,
    validation_target: Option<HarnessValidationTarget>,
}

impl CompilerRunner {
    pub fn new(output_path: PathBuf) -> Self {
        Self {
            output_path,
            validation_target: None,
        }
    }

    pub fn with_validation_target(mut self, target: Option<HarnessValidationTarget>) -> Self {
        self.validation_target = target.filter(|target| target.is_active());
        self
    }

    pub fn is_forge_available(&self) -> bool {
        std::process::Command::new("forge")
            .arg("--version")
            .output()
            .is_ok()
    }

    pub fn reset_log(&self) -> Result<(), std::io::Error> {
        let log_file = self.build_log_path();
        if let Some(parent) = log_file.parent() {
            std::fs::create_dir_all(parent)?;
        }
        let _ = std::fs::write(
            log_file,
            format!(
                "[*] Solidity Resurrector compile log\n[*] Target: {}\n",
                self.output_path.display()
            ),
        );
        Ok(())
    }

    pub async fn run_compile(&self, phase: &str) -> (bool, String, String) {
        let output_dir = self
            .output_path
            .parent()
            .unwrap_or(std::path::Path::new("."));
        let target_path = match self.output_path.canonicalize() {
            Ok(path) => path,
            Err(_) => self.output_path.clone(),
        };
        let target_name = match target_path.file_name().and_then(|name| name.to_str()) {
            Some(name) => name.to_string(),
            None => {
                let message = format!(
                    "Invalid Solidity output path: {}",
                    self.output_path.display()
                );
                self.append_build_log(phase, "forge build <target> --via-ir", false, &message);
                return (false, message, "forge build <target> --via-ir".to_string());
            }
        };
        let target_arg = target_path.to_string_lossy().to_string();

        if let Some(validation_target) = &self.validation_target {
            let isolated = match prepare_isolated_foundry_project(&target_path, output_dir) {
                Ok(project) => project,
                Err(e) => {
                    self.append_build_log(
                        phase,
                        "forge test <isolated-target> --match-contract <target> --match-test <entry> --via-ir",
                        false,
                        &e,
                    );
                    return (
                        false,
                        e,
                        "forge test <isolated-target> --match-contract <target> --match-test <entry> --via-ir".to_string(),
                    );
                }
            };
            let contract_regex = validation_target.exact_contract_regex();
            let test_regex = validation_target.exact_test_regex();
            let cmd_str = format!(
                "forge test --root {} --match-contract {} --match-test {} --via-ir",
                isolated.display(),
                contract_regex,
                test_regex
            );
            crate::execution_log::log_line(format!("compile phase={} command={}", phase, cmd_str));

            let output = Command::new("forge")
                .arg("test")
                .arg("--root")
                .arg(&isolated)
                .arg("--match-contract")
                .arg(&contract_regex)
                .arg("--match-test")
                .arg(&test_regex)
                .arg("--via-ir")
                .current_dir(&isolated)
                .output()
                .await;

            return match output {
                Ok(output) => {
                    let stdout = String::from_utf8_lossy(&output.stdout);
                    let stderr = String::from_utf8_lossy(&output.stderr);
                    let combined = format!("{}{}", stdout, stderr);
                    let success = output.status.success() && self.is_target_test_success(&combined);
                    self.append_build_log(phase, &cmd_str, success, &combined);
                    (success, combined, cmd_str)
                }
                Err(e) => {
                    let message = format!("Command failed: {}", e);
                    self.append_build_log(phase, &cmd_str, false, &message);
                    (false, message, cmd_str)
                }
            };
        }

        let cmd_str = format!("forge build {} --via-ir", target_arg);
        crate::execution_log::log_line(format!("compile phase={} command={}", phase, cmd_str));

        let output = Command::new("forge")
            .arg("build")
            .arg(&target_arg)
            .arg("--via-ir")
            .current_dir(output_dir)
            .output()
            .await;

        match output {
            Ok(output) => {
                let stdout = String::from_utf8_lossy(&output.stdout);
                let stderr = String::from_utf8_lossy(&output.stderr);
                let combined = format!("{}{}", stdout, stderr);
                let success = output.status.success()
                    && self.is_target_compile_success(&combined, &target_name);
                self.append_build_log(phase, &cmd_str, success, &combined);
                (success, combined, cmd_str)
            }
            Err(e) => {
                let message = format!("Command failed: {}", e);
                self.append_build_log(phase, &cmd_str, false, &message);
                (false, message, cmd_str)
            }
        }
    }

    fn append_build_log(&self, phase: &str, command: &str, success: bool, output: &str) {
        let log_file = self.build_log_path();
        if let Some(parent) = log_file.parent() {
            let _ = std::fs::create_dir_all(parent);
        }
        if let Ok(mut file) = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&log_file)
        {
            let _ = writeln!(file, "\n=== {} ===", phase);
            let _ = writeln!(file, "command: {}", command);
            let _ = writeln!(file, "success: {}", success);
            let _ = writeln!(file, "--- compiler output ---");
            let _ = writeln!(file, "{}", output.trim_end());
            let _ = writeln!(file, "--- end compiler output ---");
        }

        crate::execution_log::log_line(format!(
            "compile phase={} success={} build_log={}",
            phase,
            success,
            log_file.display()
        ));
        if !success {
            crate::execution_log::log_block("compiler failure output", output);
        }
    }

    fn build_log_path(&self) -> PathBuf {
        if let Ok(path) = std::env::var("SC_SLICER_BUILD_LOG_FILE") {
            if !path.trim().is_empty() {
                return PathBuf::from(path);
            }
        }

        let mut path = self.output_path.clone();
        let build_name = self
            .output_path
            .file_stem()
            .and_then(|stem| stem.to_str())
            .map(|stem| format!("{}.build.log", stem))
            .unwrap_or_else(|| "build.log".to_string());
        path.set_file_name(build_name);
        path
    }

    fn is_target_compile_success(&self, compiler_output: &str, target_name: &str) -> bool {
        let lower = compiler_output.to_lowercase();
        if lower.contains("error") || lower.contains("failed") {
            return false;
        }

        // Foundry should explicitly report a successful compiler run for the target build.
        // A zero exit code without this signal can be a false positive when no contracts were compiled.
        if !compiler_output.contains("Compiler run successful") {
            return false;
        }

        self.output_path.exists()
            && self.output_path.extension().and_then(|ext| ext.to_str()) == Some("sol")
            && !target_name.trim().is_empty()
    }

    fn is_target_test_success(&self, test_output: &str) -> bool {
        let lower = test_output.to_lowercase();
        if lower.contains("compiler run failed")
            || lower.contains("error:")
            || lower.contains("no tests match")
            || lower.contains("no tests found")
        {
            return false;
        }

        lower.contains("suite result: ok")
            || lower.contains("test result: ok")
            || lower.contains("passed; 0 failed")
    }

    pub fn extract_solidity_errors(&self, compiler_output: &str) -> Vec<String> {
        let structured = self.extract_structured_errors(compiler_output);
        if !structured.is_empty() {
            return structured
                .into_iter()
                .map(|err| {
                    let location = match (&err.file, err.line, err.column) {
                        (Some(file), Some(line), Some(column)) => {
                            format!(" at {}:{}:{}", file.display(), line, column)
                        }
                        _ => String::new(),
                    };
                    let code = err
                        .code
                        .as_ref()
                        .map(|code| format!(" ({})", code))
                        .unwrap_or_default();
                    let snippet_text = if !err.snippet.is_empty() {
                        format!("\n{}", err.snippet.join("\n"))
                    } else {
                        String::new()
                    };
                    format!(
                        "{:?}{}: {}{}{}",
                        err.category, code, err.message, location, snippet_text
                    )
                })
                .collect();
        }

        let mut errors = Vec::new();
        for line in compiler_output.lines() {
            let trimmed = line.trim();
            if trimmed.to_lowercase().contains("error") {
                errors.push(trimmed.to_string());
            }
        }
        if errors.is_empty() && !compiler_output.is_empty() {
            if let Some(first_line) = compiler_output.lines().next() {
                errors.push(first_line.to_string());
            }
        }
        errors
    }

    pub fn extract_structured_errors(&self, compiler_output: &str) -> Vec<CompilerError> {
        let lines: Vec<&str> = compiler_output.lines().collect();
        let mut errors = Vec::new();
        let mut idx = 0;

        while idx < lines.len() {
            let trimmed = lines[idx].trim();
            if let Some((code, message)) = parse_error_header(trimmed) {
                let mut err = CompilerError {
                    code,
                    category: classify_error(&message),
                    message,
                    file: None,
                    line: None,
                    column: None,
                    snippet: Vec::new(),
                };

                let mut lookahead = idx + 1;
                while lookahead < lines.len() && lookahead <= idx + 8 {
                    let candidate = lines[lookahead].trim();

                    if lookahead > idx + 1 && parse_error_header(candidate).is_some() {
                        break;
                    }

                    if let Some((file, line, column)) = parse_location(candidate) {
                        err.file = Some(file);
                        err.line = Some(line);
                        err.column = Some(column);
                    } else if !candidate.is_empty()
                        && !candidate.starts_with('|')
                        && !candidate.starts_with('=')
                    {
                        err.snippet.push(candidate.to_string());
                    }

                    lookahead += 1;
                }

                errors.push(err);
                idx = lookahead;
                continue;
            }

            idx += 1;
        }

        errors
    }
}

fn prepare_isolated_foundry_project(
    target_path: &Path,
    output_dir: &Path,
) -> Result<PathBuf, String> {
    let file_name = target_path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| format!("Invalid target path: {}", target_path.display()))?;
    let sanitized = file_name
        .chars()
        .map(|ch| {
            if ch.is_ascii_alphanumeric() || ch == '_' || ch == '.' || ch == '-' {
                ch
            } else {
                '_'
            }
        })
        .collect::<String>();
    let project_dir = std::env::temp_dir().join(format!(
        "sc_slicer_forge_{}_{}",
        std::process::id(),
        sanitized
    ));
    std::fs::create_dir_all(&project_dir)
        .map_err(|e| format!("Failed to create isolated forge dir: {}", e))?;

    let target_copy = project_dir.join(file_name);
    std::fs::copy(target_path, &target_copy)
        .map_err(|e| format!("Failed to copy target harness for forge validation: {}", e))?;

    let source_foundry = output_dir.join("foundry.toml");
    let foundry_toml = if source_foundry.exists() {
        std::fs::read_to_string(&source_foundry)
            .map_err(|e| format!("Failed to read foundry.toml: {}", e))?
    } else {
        "[profile.default]\nsrc = \".\"\ntest = \".\"\nout = \"out\"\ncache_path = \"cache\"\nauto_detect_solc = true\nevm_version = \"cancun\"\noptimizer = true\noptimizer_runs = 200\nvia_ir = true\n".to_string()
    };
    std::fs::write(project_dir.join("foundry.toml"), foundry_toml)
        .map_err(|e| format!("Failed to write isolated foundry.toml: {}", e))?;

    Ok(project_dir)
}

fn exact_solidity_identifier_regex(identifier: &str) -> String {
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

fn parse_error_header(line: &str) -> Option<(Option<String>, String)> {
    if let Some(rest) = line.strip_prefix("Error (") {
        let (code, message) = rest.split_once("): ")?;
        return Some((Some(code.to_string()), message.to_string()));
    }

    if let Some(rest) = line.strip_prefix("Error: ") {
        if rest == "Compiler run failed:" {
            return None;
        }
        return Some((None, rest.to_string()));
    }

    None
}

fn parse_location(line: &str) -> Option<(PathBuf, usize, usize)> {
    let rest = line.strip_prefix("--> ")?;
    let rest = rest.strip_suffix(':').unwrap_or(rest);
    let mut parts = rest.rsplitn(3, ':');
    let column = parts.next()?.parse().ok()?;
    let line_no = parts.next()?.parse().ok()?;
    let file = parts.next()?;
    Some((PathBuf::from(file), line_no, column))
}

fn classify_error(message: &str) -> CompilerErrorCategory {
    let lower = message.to_lowercase();
    if lower.contains("expected")
        || lower.contains("unexpected")
        || lower.contains("parsererror")
        || lower.contains("syntax")
    {
        CompilerErrorCategory::Syntax
    } else if lower.contains("already declared") || lower.contains("identifier already declared") {
        CompilerErrorCategory::Duplicate
    } else if lower.contains("undeclared identifier")
        || lower.contains("identifier not found")
        || lower.contains("not found")
    {
        CompilerErrorCategory::MissingSymbol
    } else if lower.contains("declarationerror") || lower.contains("declaration") {
        CompilerErrorCategory::Declaration
    } else if lower.contains("typeerror") || lower.contains("type ") {
        CompilerErrorCategory::Type
    } else {
        CompilerErrorCategory::Other
    }
}
