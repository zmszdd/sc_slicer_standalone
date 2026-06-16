#![allow(unused)]
pub mod assembler;
pub mod ast_extractor;
pub mod brain;
pub mod compiler_runner;
pub mod extractor;
pub mod normalizer;

pub use brain::RepairGuidance;
pub use compiler_runner::HarnessValidationTarget;
use compiler_runner::{CompilerError, CompilerErrorCategory};
use std::collections::{HashMap, HashSet};
use std::path::Path;

#[derive(Clone, Debug)]
struct SourceFunction {
    container_name: Option<String>,
    name: String,
    param_count: Option<usize>,
    body_hash: u64,
    source: String,
}

#[derive(Clone, Debug)]
struct SourceContainer {
    name: String,
    kind: String,
    body_hash: u64,
    source: String,
}

#[derive(Default)]
struct SourceIndex {
    functions: Vec<SourceFunction>,
    containers: HashMap<String, SourceContainer>,
    members_by_symbol: HashMap<String, HashSet<String>>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
enum RestoreKind {
    SlicedOutput,
    SourceBackedStatement,
    SourceBackedFunction,
    SourceBackedContainer,
}

#[derive(Clone, Debug)]
struct OutputLineProvenance {
    output_line: usize,
    chunk_id: Option<String>,
    chunk_local_line: Option<usize>,

    source_id: Option<String>,
    original_start_line: Option<usize>,
    original_end_line: Option<usize>,

    container: Option<String>,
    function: Option<String>,
    param_count: Option<usize>,

    statement_hash: Option<String>,
    statement_start_line: Option<usize>,
    statement_end_line: Option<usize>,

    restore_kind: RestoreKind,
}

#[derive(Clone, Debug)]
struct OutputLineProvenanceMap {
    lines: Vec<OutputLineProvenance>,
}

impl OutputLineProvenanceMap {
    fn build(
        code: &str,
        protected_statements: &[StatementReplacement],
        protected_functions: &[SourceReplacement],
        protected_containers: &[ContainerReplacement],
    ) -> Self {
        let raw_lines: Vec<&str> = code.lines().collect();
        let mut lines = Vec::with_capacity(raw_lines.len());

        for idx in 0..raw_lines.len() {
            let line_no = idx + 1;
            let container =
                find_enclosing_container_start(&raw_lines, line_no).and_then(|container_idx| {
                    parse_container_name(raw_lines[container_idx].trim_start())
                });
            let function_start = find_enclosing_function_start(&raw_lines, line_no);
            let function = function_start
                .and_then(|function_idx| parse_function_name(raw_lines[function_idx].trim_start()));
            let param_count = function_start
                .and_then(|function_idx| function_param_count_from_lines(&raw_lines, function_idx));

            let restore_kind = if protected_containers.iter().any(|replacement| {
                container.as_deref() == Some(replacement.container_name.as_str())
            }) {
                RestoreKind::SourceBackedContainer
            } else if protected_statements.iter().any(|replacement| {
                replacement.container_name.as_deref() == container.as_deref()
                    && Some(replacement.function_name.as_str()) == function.as_deref()
                    && replacement.param_count == param_count
            }) {
                RestoreKind::SourceBackedStatement
            } else if protected_functions.iter().any(|replacement| {
                replacement.container_name.as_deref() == container.as_deref()
                    && Some(replacement.function_name.as_str()) == function.as_deref()
                    && replacement.param_count == param_count
            }) {
                RestoreKind::SourceBackedFunction
            } else {
                RestoreKind::SlicedOutput
            };

            let source_id = container.as_ref().map(|container| match function.as_ref() {
                Some(function) => format!("{}::{}", container, function),
                None => container.clone(),
            });

            lines.push(OutputLineProvenance {
                output_line: line_no,
                chunk_id: None,
                chunk_local_line: None,
                source_id,
                original_start_line: None,
                original_end_line: None,
                container,
                function,
                param_count,
                statement_hash: None,
                statement_start_line: None,
                statement_end_line: None,
                restore_kind,
            });
        }

        Self { lines }
    }

    fn get(&self, line_no: usize) -> Option<&OutputLineProvenance> {
        self.lines.get(line_no.saturating_sub(1))
    }
}

impl SourceIndex {
    fn build(source: &str) -> Self {
        let lines: Vec<&str> = source.lines().collect();
        let mut functions = Vec::new();
        let mut containers = HashMap::new();
        let mut members_by_symbol: HashMap<String, HashSet<String>> = HashMap::new();

        for (idx, line) in lines.iter().enumerate() {
            let trimmed = line.trim_start();
            if let Some((kind, name)) = normalizer::parse_top_level_definition(trimmed) {
                if matches!(
                    kind,
                    "contract" | "abstract contract" | "interface" | "library"
                ) {
                    if let Some(container_end) = find_block_end(&lines, idx) {
                        let source = lines[idx..=container_end].join("\n");
                        containers.insert(
                            name.to_string(),
                            SourceContainer {
                                name: name.to_string(),
                                kind: kind.to_string(),
                                body_hash: stable_hash(&source),
                                source: source.clone(),
                            },
                        );
                        index_container_members(name, &source, &mut members_by_symbol);
                    }
                }
            }

            if !trimmed.starts_with("function ") {
                continue;
            }

            let Some(name) = parse_function_name(trimmed) else {
                continue;
            };
            let Some(function_end) = find_function_end(&lines, idx) else {
                continue;
            };
            let container_name = find_enclosing_container_start(&lines, idx + 1)
                .and_then(|container_idx| parse_container_name(lines[container_idx].trim_start()));
            let source = lines[idx..=function_end].join("\n");

            functions.push(SourceFunction {
                container_name,
                name,
                param_count: function_param_count_from_lines(&lines, idx),
                body_hash: stable_hash(&source),
                source,
            });
        }

        Self {
            functions,
            containers,
            members_by_symbol,
        }
    }

    fn function(
        &self,
        container_name: Option<&str>,
        function_name: &str,
        preferred_param_count: Option<usize>,
    ) -> Option<&SourceFunction> {
        let mut fallback = None;
        for function in &self.functions {
            if function.name != function_name {
                continue;
            }
            if let Some(container_name) = container_name {
                if function.container_name.as_deref() != Some(container_name) {
                    continue;
                }
            }

            if preferred_param_count.is_some() && function.param_count == preferred_param_count {
                return Some(function);
            }

            fallback.get_or_insert(function);
        }

        fallback
    }

    fn container(&self, container_name: &str) -> Option<&SourceContainer> {
        self.containers.get(container_name)
    }

    fn functions_in_container(&self, container_name: &str) -> Vec<&SourceFunction> {
        self.functions
            .iter()
            .filter(|function| function.container_name.as_deref() == Some(container_name))
            .collect()
    }

    fn providers_for_symbol(&self, symbol: &str) -> Vec<String> {
        self.members_by_symbol
            .get(symbol)
            .map(|providers| {
                let mut providers = providers.iter().cloned().collect::<Vec<_>>();
                providers.sort();
                providers
            })
            .unwrap_or_default()
    }
}

#[derive(Clone, Debug, Hash, PartialEq, Eq)]
struct SourceReplacement {
    container_name: Option<String>,
    function_name: String,
    param_count: Option<usize>,
    expected_hash: u64,
}

#[derive(Clone, Debug, Hash, PartialEq, Eq)]
struct ContainerReplacement {
    container_name: String,
    expected_hash: u64,
}

#[derive(Clone, Debug, Hash, PartialEq, Eq)]
pub enum StatementRestoreReason {
    DanglingCallClose,
    DanglingTupleClose,
    BrokenAssertCall,
    BrokenVariableDeclaration,
    BrokenExpressionStatement,
    BrokenReturnStatement,
    Unknown,
}

#[derive(Clone, Debug, Hash, PartialEq, Eq)]
struct StatementReplacement {
    container_name: Option<String>,
    function_name: String,
    param_count: Option<usize>,
    expected_hash: u64,
    source_text: String,
    statement_hash: Option<String>,
    original_source: Option<String>,
    restored_source: Option<String>,
    reason: Option<StatementRestoreReason>,
}

#[derive(Clone, Debug, Default)]
struct RestoreHistory {
    restored_statements: HashSet<StatementReplacement>,
    restored_functions: HashSet<SourceReplacement>,
    restored_containers: HashSet<ContainerReplacement>,
    restored_missing_symbols: HashSet<MissingSymbolRestoreAction>,
    failed_statements: HashSet<StatementReplacement>,
    failed_functions: HashSet<SourceReplacement>,
    failed_containers: HashSet<ContainerReplacement>,
    failed_missing_symbols: HashSet<MissingSymbolRestoreAction>,
}

impl RestoreHistory {
    fn has_statement(&self, replacement: &StatementReplacement) -> bool {
        self.restored_statements.contains(replacement)
            || self.failed_statements.contains(replacement)
    }

    fn has_function(&self, replacement: &SourceReplacement) -> bool {
        self.restored_functions.contains(replacement) || self.failed_functions.contains(replacement)
    }

    fn has_container(&self, replacement: &ContainerReplacement) -> bool {
        self.restored_containers.contains(replacement)
            || self.failed_containers.contains(replacement)
    }

    fn has_missing_symbol(&self, replacement: &MissingSymbolRestoreAction) -> bool {
        self.restored_missing_symbols.contains(replacement)
            || self.failed_missing_symbols.contains(replacement)
    }

    fn record_success(&mut self, repair: &DeterministicRepair) {
        for replacement in &repair.statement_replacements {
            self.restored_statements.insert(replacement.clone());
        }
        for replacement in &repair.source_replacements {
            self.restored_functions.insert(replacement.clone());
        }
        for replacement in &repair.container_replacements {
            self.restored_containers.insert(replacement.clone());
        }
        for replacement in &repair.missing_symbol_replacements {
            self.restored_missing_symbols.insert(replacement.clone());
        }
    }

    fn record_failure(&mut self, repair: &DeterministicRepair) {
        for replacement in &repair.statement_replacements {
            self.failed_statements.insert(replacement.clone());
        }
        for replacement in &repair.source_replacements {
            self.failed_functions.insert(replacement.clone());
        }
        for replacement in &repair.container_replacements {
            self.failed_containers.insert(replacement.clone());
        }
        for replacement in &repair.missing_symbol_replacements {
            self.failed_missing_symbols.insert(replacement.clone());
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum MissingSymbolRestoreAction {
    RestoreFunction { container: String, name: String },
    RestoreVariable { container: String, name: String },
    RestoreLibraryMember { library: String, name: String },
    RestoreType { name: String },
}

struct DeterministicRepair {
    code: String,
    statement_replacements: Vec<StatementReplacement>,
    source_replacements: Vec<SourceReplacement>,
    container_replacements: Vec<ContainerReplacement>,
    missing_symbol_replacements: Vec<MissingSymbolRestoreAction>,
    source_backed: bool,
}

impl DeterministicRepair {
    fn plain(code: String) -> Self {
        Self {
            code,
            statement_replacements: Vec::new(),
            source_replacements: Vec::new(),
            container_replacements: Vec::new(),
            missing_symbol_replacements: Vec::new(),
            source_backed: false,
        }
    }

    fn source_backed(code: String, source_replacements: Vec<SourceReplacement>) -> Self {
        Self {
            code,
            statement_replacements: Vec::new(),
            source_replacements,
            container_replacements: Vec::new(),
            missing_symbol_replacements: Vec::new(),
            source_backed: true,
        }
    }

    fn source_backed_statements(
        code: String,
        statement_replacements: Vec<StatementReplacement>,
    ) -> Self {
        Self {
            code,
            statement_replacements,
            source_replacements: Vec::new(),
            container_replacements: Vec::new(),
            missing_symbol_replacements: Vec::new(),
            source_backed: true,
        }
    }

    fn source_backed_code(code: String) -> Self {
        Self {
            code,
            statement_replacements: Vec::new(),
            source_replacements: Vec::new(),
            container_replacements: Vec::new(),
            missing_symbol_replacements: Vec::new(),
            source_backed: true,
        }
    }

    fn source_backed_containers(
        code: String,
        source_replacements: Vec<SourceReplacement>,
        container_replacements: Vec<ContainerReplacement>,
    ) -> Self {
        Self {
            code,
            statement_replacements: Vec::new(),
            source_replacements,
            container_replacements,
            missing_symbol_replacements: Vec::new(),
            source_backed: true,
        }
    }

    fn missing_symbol_backed(
        code: String,
        missing_symbol_replacements: Vec<MissingSymbolRestoreAction>,
    ) -> Self {
        Self {
            code,
            statement_replacements: Vec::new(),
            source_replacements: Vec::new(),
            container_replacements: Vec::new(),
            missing_symbol_replacements,
            source_backed: true,
        }
    }
}

pub async fn run_resurrection(
    input_slice: &str,
    original_source: &str,
    target_output: &Path,
    api_key: &str,
    base_url: &str,
    model_name: &str,
    max_fix_iterations: usize,
    validation_target: Option<HarnessValidationTarget>,
    repair_guidance: Option<RepairGuidance>,
    ast_extraction: Option<crate::sol_resurrect_pipeline::ast_extractor::ExtractionResult>,
) -> Result<String, Box<dyn std::error::Error>> {
    println!("[*] Starting Code Resurrection Pipeline...");
    crate::execution_log::log_line(format!(
        "resurrection start target={} max_fix_iterations={}",
        target_output.display(),
        max_fix_iterations
    ));
    let source_index = SourceIndex::build(original_source);
    crate::execution_log::detail(
        "resurrection_source_index",
        format!(
            "functions={} containers={} member_symbols={}",
            source_index.functions.len(),
            source_index.containers.len(),
            source_index.members_by_symbol.len()
        ),
    );

    // Step 1: Initial Parsing
    println!("    -> Parsing initial slice...");
    crate::execution_log::log_line(format!(
        "resurrection parse initial_slice_lines={}",
        input_slice.lines().count()
    ));
    std::fs::write("/tmp/initial_slice.sol", input_slice).unwrap();
    let normalized = normalizer::normalize_source(input_slice);
    if normalized.report.has_changes() {
        println!(
            "    -> Preflight normalized {} malformed/comment lines",
            normalized.report.actions.len()
        );
        crate::execution_log::log_line(format!(
            "resurrection preflight normalized actions={}",
            normalized.report.actions.len()
        ));
    }
    let mut current_code =
        repair_orphan_multiline_expression_prefixes(&normalized.code, original_source, "preflight");
    current_code =
        repair_corrupted_containers_from_source(&current_code, original_source, "preflight");

    let mut using_source_closure_seed = false;
    if std::env::var("SC_SLICER_SOURCE_CLOSURE").unwrap_or_else(|_| "0".to_string()) != "0" {
        if let Some(guidance) = repair_guidance.as_ref() {
            if let Some(source_closure) =
                build_source_closure_seed(original_source, &guidance.target_contract)
            {
                println!(
                    "    -> Built source-backed dependency-closure seed for {} ({} lines).",
                    guidance.target_contract,
                    source_closure.lines().count()
                );
                crate::execution_log::log_line(format!(
                    "resurrection source_closure_seed target={} lines={}",
                    guidance.target_contract,
                    source_closure.lines().count()
                ));
                current_code = source_closure;
                using_source_closure_seed = true;
            }
        }
    }

    let brain = brain::ContextBrain::new(
        api_key.to_string(),
        base_url.to_string(),
        model_name.to_string(),
    );

    let final_guidance = repair_guidance;
    let assembler = assembler::Assembler::new();

    if using_source_closure_seed {
        println!("    -> Skipping fragment assembly for source-backed closure seed.");
        crate::execution_log::log_line(
            "resurrection source_closure_seed skipped pre-compile inference assembly",
        );
    } else {
        // Step 2: Deterministic AST/source-backed context inference.
        println!("    -> Inferring context via deterministic AST/source restoration...");
        crate::execution_log::log_line("resurrection deterministic context inference started");

        // Pass the raw code and original source to extract existing definitions.
        // The direct resurrection path keeps generation out of the pipeline:
        // AST/source-backed restoration is allowed, unresolved symbols are reported.
        if let Some(rg) = final_guidance.as_ref() {
            println!(
                "    -> Using deterministic AST/source restoration for {}.{}.",
                rg.target_contract, rg.entry_function
            );
        }

        let inference_result = brain
            .infer(
                &current_code,
                original_source,
                final_guidance.as_ref(),
                ast_extraction,
            )
            .await?;
        crate::execution_log::detail(
            "resurrection_inference",
            format!(
                "mock_libraries={} rehoming_entries={}",
                inference_result.mock_libraries.len(),
                inference_result.rehoming_map.len()
            ),
        );
        crate::execution_log::sample(
            "resurrection_inference_mock_libraries",
            inference_result.mock_libraries.keys(),
            60,
        );
        crate::execution_log::sample(
            "resurrection_inference_rehoming",
            inference_result
                .rehoming_map
                .iter()
                .map(|(from, to)| format!("{}=>{}", from, to)),
            60,
        );

        // Step 3: Assembly
        println!("    -> Assembling final code...");
        crate::execution_log::log_line("resurrection assembly started");
        current_code = assembler.assemble(&current_code, &inference_result);
        current_code = normalizer::normalize_solidity_fragment(&current_code);
        current_code =
            repair_orphan_multiline_expression_prefixes(&current_code, original_source, "assembly");
        current_code =
            repair_corrupted_containers_from_source(&current_code, original_source, "assembly");
    }

    // Repair orphaned multiline constant value continuations (e.g. `uint160 constant X =\n  123456789;`)
    // before writing to disk so that the initial forge compile validation has the correct code.
    current_code =
        repair_dangling_value_continuations(&current_code, original_source, "pre-compile");

    // Save initial assembled code
    if let Some(parent) = target_output.parent() {
        std::fs::create_dir_all(parent)?;
    }
    std::fs::write(target_output, &current_code)?;
    println!("    -> Output written to {}", target_output.display());
    crate::execution_log::log_line(format!(
        "resurrection initial output written path={} lines={}",
        target_output.display(),
        current_code.lines().count()
    ));
    let baseline_output_lines = current_code.lines().count();

    // Step 4: Compiler Repair Loop
    let runner = compiler_runner::CompilerRunner::new(target_output.to_path_buf())
        .with_validation_target(validation_target.clone());

    if !runner.is_forge_available() {
        println!("[WARN] forge not found; skipping automatic compilation and repair loop.");
        crate::execution_log::log_line(
            "resurrection compile validation skipped because forge was not found",
        );
        return Ok(current_code);
    }

    println!("[*] Starting automatic compile validation...");
    crate::execution_log::log_line("resurrection compile validation started");
    runner.reset_log()?;

    let (mut success, mut output, mut cmd) = runner.run_compile("initial validation").await;
    if success {
        println!("[SUCCESS] Compile passed via: {}", cmd);
        crate::execution_log::log_line(format!(
            "resurrection compile success phase=initial command={}",
            cmd
        ));
        return Ok(current_code);
    } else {
        println!("[WARN] Initial compile failed via: {}", cmd);
        crate::execution_log::log_line(format!(
            "resurrection compile failed phase=initial command={}",
            cmd
        ));
    }

    // P0: Track error fingerprints to detect repair loops
    let mut seen_error_fingerprints: Vec<String> = Vec::new();
    let mut consecutive_no_progress = 0usize;
    let mut protected_statement_replacements: Vec<StatementReplacement> = Vec::new();
    let mut protected_source_replacements: Vec<SourceReplacement> = Vec::new();
    let mut protected_container_replacements: Vec<ContainerReplacement> = Vec::new();
    let mut restore_history = RestoreHistory::default();
    let effective_max_fix_iterations = max_fix_iterations;

    for attempt in 1..=effective_max_fix_iterations {
        if success {
            break;
        }
        println!(
            "[*] Auto-repair iteration {}/{}",
            attempt, effective_max_fix_iterations
        );
        println!("    -> Failure reason:");
        crate::execution_log::log_line(format!(
            "resurrection repair iteration {}/{} started",
            attempt, effective_max_fix_iterations
        ));
        let structured_errors = runner.extract_structured_errors(&output);
        log_compiler_errors_for_attempt(attempt, &structured_errors, &runner, &output);
        if structured_errors.is_empty() {
            let errors = runner.extract_solidity_errors(&output);
            for err in errors.iter().take(8) {
                println!("       - {}", err);
            }
        } else {
            // Re-use the nice formatting logic we just added to extract_solidity_errors
            let full_errors = runner.extract_solidity_errors(&output);
            for err_text in full_errors.iter().take(8) {
                // Split by newline and add indentation so the snippet lines up nicely
                for (i, line) in err_text.lines().enumerate() {
                    if i == 0 {
                        println!("       - {}", line);
                    } else {
                        println!("         {}", line);
                    }
                }
            }
        }

        // P0: Loop detection — compute error fingerprint and check for repeats
        let error_fingerprint =
            compute_logical_error_fingerprint(&structured_errors, &current_code);
        crate::execution_log::detail(
            "resurrection_error_fingerprint",
            format!(
                "attempt={} fingerprint={}",
                attempt,
                &error_fingerprint[..error_fingerprint.len().min(240)]
            ),
        );
        let mut repeated_error_count = 1usize;
        let mut repeated_error_should_stop_if_unrepaired = false;
        if seen_error_fingerprints.contains(&error_fingerprint) {
            consecutive_no_progress += 1;
            repeated_error_count = consecutive_no_progress + 1;
            println!(
                "[WARN] Detected repeated error pattern (seen {} times). Error fingerprint: {}",
                repeated_error_count,
                &error_fingerprint[..error_fingerprint.len().min(120)]
            );
            let repeated_missing_symbol = structured_errors
                .iter()
                .any(|err| err.category == CompilerErrorCategory::MissingSymbol);
            if consecutive_no_progress >= 2 && !repeated_missing_symbol {
                println!(
                    "[WARN] Same error pattern repeated {} times; deterministic restore will be tried before stopping.",
                    repeated_error_count
                );
                crate::execution_log::log_line(format!(
                    "resurrection repair loop repeated_pattern_pending_restore repeated_error_count={}",
                    repeated_error_count
                ));
                repeated_error_should_stop_if_unrepaired = true;
            } else if consecutive_no_progress >= 2 {
                println!(
                    "[WARN] Repeated missing-symbol pattern; continuing deterministic dependency repair."
                );
                crate::execution_log::log_line(format!(
                    "resurrection repair loop continued_missing_symbol_repeat repeated_error_count={}",
                    repeated_error_count
                ));
            }
        }
        seen_error_fingerprints.push(error_fingerprint);

        let mut repair_errors = structured_errors.clone();
        repair_errors.extend(
            runner
                .extract_solidity_errors(&output)
                .iter()
                .filter_map(|text| compiler_error_from_text(text)),
        );

        // P0: Deduplicate errors by message to avoid flooding repair logic
        repair_errors = deduplicate_errors(repair_errors);

        // P0: Sort errors by priority (Syntax first, then MissingSymbol, etc.)
        sort_errors_by_priority(&mut repair_errors);
        if repair_errors
            .iter()
            .any(is_identifier_not_library_name_error)
        {
            println!("    -> Deterministic repair received a using-library error.");
            for err in repair_errors
                .iter()
                .filter(|err| is_identifier_not_library_name_error(err))
            {
                println!(
                    "    -> using-library debug: line={:?} snippets={:?}",
                    err.line,
                    err.snippet.iter().take(3).collect::<Vec<_>>()
                );
            }
        }

        // P0: Snapshot code before deterministic repair for idempotency check
        let code_before_repair = current_code.clone();

        if let Some(repaired) = try_deterministic_syntax_repair_with_context(
            &current_code,
            &repair_errors,
            original_source,
            &source_index,
            &protected_statement_replacements,
            &protected_source_replacements,
            &protected_container_replacements,
            &restore_history,
            baseline_output_lines,
            validation_target.as_ref(),
        ) {
            let mut candidate_statement_replacements = protected_statement_replacements.clone();
            merge_unique(
                &mut candidate_statement_replacements,
                &repaired.statement_replacements,
            );
            let mut candidate_source_replacements = protected_source_replacements.clone();
            merge_unique(
                &mut candidate_source_replacements,
                &repaired.source_replacements,
            );
            let mut candidate_container_replacements = protected_container_replacements.clone();
            merge_unique(
                &mut candidate_container_replacements,
                &repaired.container_replacements,
            );
            let source_backed_protected_restore = repaired.source_backed
                && (!repaired.statement_replacements.is_empty()
                    || !repaired.source_replacements.is_empty()
                    || !repaired.container_replacements.is_empty());
            let is_source_backed_repair = repaired.source_backed;

            let repaired_normalized = if is_source_backed_repair {
                protect_replacements(
                    &repaired.code,
                    &candidate_statement_replacements,
                    &candidate_source_replacements,
                    &candidate_container_replacements,
                    &source_index,
                )
            } else {
                let repaired_normalized = normalizer::normalize_solidity_fragment(&repaired.code);
                let repaired_normalized = repair_orphan_multiline_expression_prefixes(
                    &repaired_normalized,
                    original_source,
                    "deterministic repair",
                );
                let repaired_normalized = protect_replacements(
                    &repaired_normalized,
                    &candidate_statement_replacements,
                    &candidate_source_replacements,
                    &candidate_container_replacements,
                    &source_index,
                );
                let mut protected_code = repaired_normalized.clone();
                let mut placeholders = HashMap::new();
                for (i, stmt) in candidate_statement_replacements.iter().enumerate() {
                    let placeholder = format!("uint256 __PROTECTED_STATEMENT_{}__;", i);
                    if protected_code.contains(&stmt.source_text) {
                        protected_code = protected_code.replace(&stmt.source_text, &placeholder);
                        placeholders.insert(placeholder, stmt.source_text.clone());
                    }
                }

                let mut repaired_normalized =
                    normalizer::normalize_solidity_fragment(&protected_code);

                for (placeholder, original) in placeholders {
                    repaired_normalized = repaired_normalized.replace(&placeholder, &original);
                }
                protect_replacements(
                    &repaired_normalized,
                    &candidate_statement_replacements,
                    &candidate_source_replacements,
                    &candidate_container_replacements,
                    &source_index,
                )
            };

            // P0: Idempotency check — skip if repair produced identical code
            if repaired_normalized == normalizer::normalize_solidity_fragment(&code_before_repair) {
                println!(
                    "    -> Deterministic repair produced identical code. \
                     No generated repair is allowed."
                );
                crate::execution_log::log_line(format!(
                    "resurrection deterministic repair no-op attempt={}",
                    attempt
                ));
            } else {
                println!("    -> Validating deterministic syntax cleanup before applying.");
                crate::execution_log::log_line(format!(
                    "resurrection deterministic repair candidate attempt={} before_lines={} after_lines={}",
                    attempt,
                    code_before_repair.lines().count(),
                    repaired_normalized.lines().count()
                ));

                let temp_target = temporary_repair_target_path(target_output, attempt + 10_000);
                if let Some(parent) = temp_target.parent() {
                    std::fs::create_dir_all(parent)?;
                }
                std::fs::write(&temp_target, &repaired_normalized)?;
                let temp_runner = compiler_runner::CompilerRunner::new(temp_target.clone())
                    .with_validation_target(validation_target.clone());
                let temp_result = temp_runner
                    .run_compile(&format!(
                        "temporary deterministic repair attempt {}",
                        attempt
                    ))
                    .await;

                if temp_result.0 {
                    consecutive_no_progress = 0;
                    restore_history.record_success(&repaired);
                    current_code = repaired_normalized;
                    protected_statement_replacements = candidate_statement_replacements;
                    protected_source_replacements = candidate_source_replacements;
                    protected_container_replacements = candidate_container_replacements;
                    std::fs::write(target_output, &current_code)?;
                    let _ = std::fs::remove_file(&temp_target);
                    success = true;
                    output = temp_result.1;
                    cmd = temp_result.2;
                    println!(
                        "[SUCCESS] Compile passed via validated deterministic patch: {}",
                        cmd
                    );
                    crate::execution_log::log_line(format!(
                        "resurrection compile success phase=deterministic_temp_validated attempt={} command={}",
                        attempt, cmd
                    ));
                    continue;
                }

                let old_errors = runner.extract_structured_errors(&output);
                let temp_errors = temp_runner.extract_structured_errors(&temp_result.1);
                let old_fingerprint = compute_logical_error_fingerprint(&old_errors, &current_code);
                let temp_fingerprint =
                    compute_logical_error_fingerprint(&temp_errors, &repaired_normalized);

                let old_score =
                    compiler_runner::CompileScore::new(&old_errors, current_code.lines().count());
                let temp_score = compiler_runner::CompileScore::new(
                    &temp_errors,
                    repaired_normalized.lines().count(),
                );
                let old_weight = old_score.weighted_total();
                let temp_weight = temp_score.weighted_total();
                let same_fingerprint = old_fingerprint == temp_fingerprint;
                let old_has_syntax = old_errors
                    .iter()
                    .any(|err| err.category == CompilerErrorCategory::Syntax);
                let source_backed_statement_restore =
                    is_source_backed_repair && !repaired.statement_replacements.is_empty();
                let restored_span_has_syntax_errors = source_backed_protected_restore
                    && syntax_errors_in_restored_spans(
                        &repaired_normalized,
                        &temp_errors,
                        &repaired.statement_replacements,
                        &repaired.source_replacements,
                        &repaired.container_replacements,
                    );
                let deterministic_lateral_progress = temp_weight <= old_weight
                    && temp_score.total <= old_score.total
                    && if old_has_syntax {
                        source_backed_protected_restore
                            && !restored_span_has_syntax_errors
                            && (!same_fingerprint || source_backed_statement_restore)
                    } else {
                        !same_fingerprint
                            && (is_source_backed_repair
                                || repaired_normalized.lines().count()
                                    <= current_code.lines().count() + 20)
                    };
                let source_backed_symbol_frontier_progress = is_source_backed_repair
                    && !restored_span_has_syntax_errors
                    && !same_fingerprint
                    && temp_score.total <= old_score.total
                    && old_errors.iter().any(|err| {
                        is_identifier_not_library_name_error(err) || is_base_precedence_error(err)
                    })
                    && temp_errors
                        .iter()
                        .any(|err| err.category == CompilerErrorCategory::MissingSymbol);
                let source_backed_base_frontier_progress = is_source_backed_repair
                    && !restored_span_has_syntax_errors
                    && !same_fingerprint
                    && temp_errors.iter().any(is_base_precedence_error);

                let score_accepts =
                    compiler_runner::should_accept_patch(&old_score, &temp_score, same_fingerprint)
                        && !(old_has_syntax
                            && source_backed_protected_restore
                            && restored_span_has_syntax_errors);

                let accept_reason = if score_accepts {
                    Some("score_improved")
                } else if deterministic_lateral_progress {
                    Some(if old_has_syntax && source_backed_statement_restore {
                        "target_statement_span_cleared"
                    } else if old_has_syntax && source_backed_protected_restore {
                        "source_restore_span_cleared"
                    } else {
                        "deterministic_lateral_progress"
                    })
                } else if source_backed_symbol_frontier_progress {
                    Some("source_backed_symbol_frontier")
                } else if source_backed_base_frontier_progress {
                    Some("source_backed_base_frontier")
                } else {
                    None
                };

                if accept_reason.is_some() {
                    println!(
                        "    -> Deterministic patch accepted (reason={}, Score: {} -> {} wt, {} -> {} errs); applying and continuing.",
                        accept_reason.unwrap_or("unknown"),
                        old_weight,
                        temp_weight,
                        old_score.total,
                        temp_score.total
                    );
                    crate::execution_log::log_line(format!(
                        "resurrection deterministic repair accepted attempt={} reason={} old_wt={} temp_wt={}",
                        attempt,
                        accept_reason.unwrap_or("unknown"),
                        old_score.weighted_total(),
                        temp_score.weighted_total()
                    ));
                    consecutive_no_progress = 0;
                    restore_history.record_success(&repaired);
                    current_code = repaired_normalized;
                    protected_statement_replacements = candidate_statement_replacements;
                    protected_source_replacements = candidate_source_replacements;
                    protected_container_replacements = candidate_container_replacements;
                    std::fs::write(target_output, &current_code)?;
                    success = false;
                    output = temp_result.1;
                    cmd = temp_result.2;
                    let _ = std::fs::remove_file(&temp_target);
                    continue;
                }

                if restored_span_has_syntax_errors {
                    println!(
                        "    -> Source-backed restore left syntax error inside restored span; marking restore unresolved."
                    );
                    crate::execution_log::log_line(format!(
                        "resurrection source restore unresolved attempt={}",
                        attempt
                    ));
                    restore_history.record_failure(&repaired);
                }

                println!("    -> Deterministic patch did not validate or reduce errors.");
                crate::execution_log::log_line(format!(
                    "resurrection deterministic repair rejected attempt={} old_errors={} temp_errors={}",
                    attempt,
                    old_errors.len(),
                    temp_errors.len()
                ));
                let _ = std::fs::remove_file(&temp_target);
            }
        }

        if repeated_error_should_stop_if_unrepaired {
            println!(
                "[WARN] Breaking repair loop: same error pattern repeated {} times and no deterministic restore was accepted.",
                repeated_error_count
            );
            crate::execution_log::log_line(format!(
                "resurrection repair loop stopped repeated_error_count={}",
                repeated_error_count
            ));
        } else {
            println!(
                "    -> No allowed deterministic repair was accepted; stopping without LLM repair."
            );
            crate::execution_log::log_line(format!(
                "resurrection repair stopped_no_llm attempt={}",
                attempt
            ));
        }
        break;
    }

    if success {
        crate::execution_log::log_line("resurrection finished with compile success");
    } else {
        let errors = runner.extract_solidity_errors(&output);
        crate::execution_log::log_line(format!(
            "resurrection finished without compile success last_command={} remaining_errors={}",
            cmd,
            errors.len()
        ));
        for err in errors.iter().take(8) {
            crate::execution_log::log_line(format!("remaining compiler error: {}", err));
        }

        let fallback_code = build_compile_stability_fallback(
            &current_code,
            &runner.extract_structured_errors(&output),
        );
        if fallback_code != current_code {
            crate::execution_log::log_line(format!(
                "resurrection compile stability fallback candidate fallback_lines={}",
                fallback_code.lines().count()
            ));

            let temp_target =
                temporary_repair_target_path(target_output, effective_max_fix_iterations + 20_000);
            if let Some(parent) = temp_target.parent() {
                std::fs::create_dir_all(parent)?;
            }
            std::fs::write(&temp_target, &fallback_code)?;
            let temp_runner = compiler_runner::CompilerRunner::new(temp_target.clone())
                .with_validation_target(validation_target.clone());
            let temp_result = temp_runner
                .run_compile("temporary compile stability fallback")
                .await;

            if temp_result.0 {
                crate::execution_log::log_line(format!(
                    "resurrection compile stability fallback validated command={}",
                    temp_result.2
                ));
                std::fs::write(target_output, &fallback_code)?;
                current_code = fallback_code;
            } else {
                let old_errors = runner.extract_structured_errors(&output);
                let temp_errors = temp_runner.extract_structured_errors(&temp_result.1);
                if temp_errors.len() < old_errors.len() {
                    crate::execution_log::log_line(format!(
                        "resurrection compile stability fallback reduced errors old_errors={} temp_errors={}",
                        old_errors.len(),
                        temp_errors.len()
                    ));
                    std::fs::write(target_output, &fallback_code)?;
                    current_code = fallback_code;
                } else {
                    crate::execution_log::log_line(format!(
                        "resurrection compile stability fallback rejected old_errors={} temp_errors={}",
                        old_errors.len(),
                        temp_errors.len()
                    ));
                }
            }
            let _ = std::fs::remove_file(&temp_target);
        }
    }

    Ok(current_code)
}

fn stable_hash(text: &str) -> u64 {
    use std::hash::{Hash, Hasher};
    let normalized = text.split_whitespace().collect::<Vec<_>>().join(" ");
    let mut hasher = std::collections::hash_map::DefaultHasher::new();
    normalized.hash(&mut hasher);
    hasher.finish()
}

fn build_source_closure_seed(original_source: &str, target_contract: &str) -> Option<String> {
    let target_contract = target_contract.trim();
    if target_contract.is_empty() {
        return None;
    }

    let mut parts = Vec::new();
    let headers = source_headers(original_source);
    if !headers.trim().is_empty() {
        parts.push(headers);
    }

    let target = extract_top_level_definition_from_source(original_source, target_contract)?;
    parts.push(target);

    Some(parts.join("\n\n"))
}

fn source_headers(source: &str) -> String {
    source
        .lines()
        .filter_map(|line| {
            let trimmed = line.trim_start();
            if trimmed.starts_with("// SPDX-License-Identifier:")
                || trimmed.starts_with("pragma ")
                || trimmed.starts_with("import ")
            {
                Some(line.to_string())
            } else {
                None
            }
        })
        .collect::<Vec<_>>()
        .join("\n")
}

fn top_level_using_directives(source: &str) -> String {
    let mut tracker = DepthTracker::default();
    let mut out = Vec::new();
    for line in source.lines() {
        if tracker.depth == 0 && line.trim_start().starts_with("using ") {
            out.push(line.to_string());
        }
        tracker.process_line_and_check_end(line);
    }
    out.join("\n")
}

fn merge_unique<T>(target: &mut Vec<T>, additions: &[T])
where
    T: Clone + PartialEq,
{
    for addition in additions {
        if !target.contains(addition) {
            target.push(addition.clone());
        }
    }
}

fn build_compile_stability_fallback(code: &str, errors: &[CompilerError]) -> String {
    let lines: Vec<&str> = code.lines().collect();
    let mut deleted = std::collections::HashSet::new();

    for err in errors {
        let Some(line_no) = err.line else {
            continue;
        };
        let idx = line_no.saturating_sub(1);
        let Some(line) = lines.get(idx) else {
            continue;
        };
        let trimmed = line.trim();

        if normalizer::is_removable_residue_line(trimmed)
            || is_statement_fragment(trimmed)
            || is_dangling_closing_call(trimmed)
            || (err.category == CompilerErrorCategory::Syntax && looks_like_parser_error(err))
        {
            deleted.insert(idx);
        }
    }

    if deleted.is_empty() {
        return code.to_string();
    }

    let mut new_code = String::new();
    for (i, line) in lines.iter().enumerate() {
        if deleted.contains(&i) {
            // P1: Use empty line instead of comment to avoid parser confusion
            // when deleted line is in the middle of a multiline statement
            new_code.push('\n');
        } else {
            new_code.push_str(line);
            new_code.push('\n');
        }
    }

    new_code.trim_end().to_string() + "\n"
}

fn index_container_members(
    container_name: &str,
    container_source: &str,
    members_by_symbol: &mut HashMap<String, HashSet<String>>,
) {
    let mut tracker = DepthTracker::default();
    for line in container_source.lines() {
        if tracker.depth == 1 {
            for symbol in declared_symbols_on_member_line(line) {
                members_by_symbol
                    .entry(symbol)
                    .or_default()
                    .insert(container_name.to_string());
            }
        }
        tracker.process_line_and_check_end(line);
    }
}

fn declared_symbols_on_member_line(line: &str) -> Vec<String> {
    let trimmed = line.trim_start();
    if trimmed.starts_with("//") || trimmed.starts_with("/*") || trimmed.starts_with('*') {
        return Vec::new();
    }
    for keyword in [
        "function ",
        "modifier ",
        "event ",
        "error ",
        "struct ",
        "enum ",
    ] {
        if let Some(rest) = trimmed.strip_prefix(keyword) {
            let name = rest
                .split(|ch: char| ch == '(' || ch == '{' || ch == ';' || ch.is_whitespace())
                .next()
                .unwrap_or("");
            if !name.is_empty() {
                return vec![name.to_string()];
            }
        }
    }
    if !trimmed.ends_with(';') || trimmed.contains(";") && trimmed.contains("function ") {
        return Vec::new();
    }
    let before_assignment = trimmed
        .split('=')
        .next()
        .unwrap_or(trimmed)
        .trim_end_matches(';');
    let tokens = before_assignment
        .split(|ch: char| ch.is_whitespace() || ch == ',' || ch == ')')
        .filter(|token| !token.is_empty())
        .collect::<Vec<_>>();
    tokens
        .last()
        .filter(|symbol| is_identifier(symbol) && !is_solidity_keyword(symbol))
        .map(|symbol| vec![(*symbol).to_string()])
        .unwrap_or_default()
}

fn finalize_repair_candidate(mut code: String, original_source: &str, stage: &str) -> String {
    code = normalizer::normalize_solidity_fragment(&code);
    code = repair_orphan_multiline_expression_prefixes(&code, original_source, stage);
    code
}

fn temporary_repair_target_path(target_output: &Path, attempt: usize) -> std::path::PathBuf {
    let file_name = target_output
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or("resurrected.sol");
    let temp_name = format!(".tmp_repair_{}_{}", attempt, file_name);
    target_output
        .parent()
        .unwrap_or_else(|| Path::new("."))
        .join(temp_name)
}

fn log_compiler_errors_for_attempt(
    attempt: usize,
    structured_errors: &[CompilerError],
    runner: &compiler_runner::CompilerRunner,
    compiler_output: &str,
) {
    if structured_errors.is_empty() {
        let errors = runner.extract_solidity_errors(compiler_output);
        crate::execution_log::detail(
            "resurrection_compiler_errors",
            format!(
                "attempt={} structured=0 fallback_errors={}",
                attempt,
                errors.len()
            ),
        );
        crate::execution_log::sample(
            "resurrection_compiler_error_fallback_sample",
            errors.iter().map(|error| compact_log_text(error, 260)),
            8,
        );
        return;
    }

    let mut counts: HashMap<&'static str, usize> = HashMap::new();
    let mut samples = Vec::new();
    for error in structured_errors {
        *counts
            .entry(error_category_name(&error.category))
            .or_default() += 1;
        let location = match (&error.file, error.line, error.column) {
            (Some(file), Some(line), Some(column)) => {
                format!("{}:{}:{}", file.display(), line, column)
            }
            _ => "<unknown>".to_string(),
        };
        samples.push(format!(
            "{} code={} location={} message={}",
            error_category_name(&error.category),
            error.code.as_deref().unwrap_or("<none>"),
            location,
            compact_log_text(&error.message, 220)
        ));
    }
    crate::execution_log::detail(
        "resurrection_compiler_errors",
        format!(
            "attempt={} structured={} category_counts={}",
            attempt,
            structured_errors.len(),
            format_log_counts(&counts)
        ),
    );
    crate::execution_log::sample("resurrection_compiler_error_sample", samples, 12);
}

fn log_repair_plan_summary(attempt: usize, repair_plan: &serde_json::Value) {
    let append_code = repair_plan
        .get("code_to_append")
        .and_then(|value| value.as_str())
        .unwrap_or("");
    let append_defs = normalizer::top_level_definition_names(append_code);
    crate::execution_log::detail(
        "resurrection_repair_plan",
        format!(
            "attempt={} keys={} append_chars={} append_lines={} append_defs={}",
            attempt,
            repair_plan
                .as_object()
                .map(|object| object.len())
                .unwrap_or(0),
            append_code.len(),
            append_code.lines().count(),
            append_defs.len()
        ),
    );
    crate::execution_log::sample("resurrection_repair_plan_defs", append_defs, 40);
}

fn error_category_name(category: &CompilerErrorCategory) -> &'static str {
    match category {
        CompilerErrorCategory::Syntax => "Syntax",
        CompilerErrorCategory::Declaration => "Declaration",
        CompilerErrorCategory::Type => "Type",
        CompilerErrorCategory::Duplicate => "Duplicate",
        CompilerErrorCategory::MissingSymbol => "MissingSymbol",
        CompilerErrorCategory::Other => "Other",
    }
}

fn format_log_counts(counts: &HashMap<&'static str, usize>) -> String {
    let mut entries = counts
        .iter()
        .map(|(name, count)| format!("{}={}", name, count))
        .collect::<Vec<_>>();
    entries.sort();
    entries.join(",")
}

fn compact_log_text(text: &str, max_chars: usize) -> String {
    let one_line = text.split_whitespace().collect::<Vec<_>>().join(" ");
    if one_line.chars().count() <= max_chars {
        one_line
    } else {
        format!(
            "{}...",
            one_line.chars().take(max_chars).collect::<String>()
        )
    }
}

pub enum DanglingCloserKind {
    CallClose,
    TupleClose,
    ArrayClose,
    StructLiteralClose,
    ReturnTupleClose,
    TernaryTail,
}

pub fn is_structural_dangling_fragment(line: &str) -> bool {
    let s = line.trim();
    matches!(s, ");" | "]," | "];" | "," | ":" | "? \"\"" | "? ''") || s.starts_with(");")
}

pub fn classify_dangling_closer(line: &str) -> DanglingCloserKind {
    let s = line.trim();
    if s.starts_with(");") {
        return DanglingCloserKind::CallClose;
    }
    if s.starts_with("),") {
        return DanglingCloserKind::TupleClose;
    }
    if s.starts_with("],") {
        return DanglingCloserKind::ArrayClose;
    }
    if s.starts_with("];") {
        return DanglingCloserKind::ArrayClose;
    }
    if s.starts_with("}") {
        return DanglingCloserKind::StructLiteralClose;
    }
    if s.starts_with(":") || s.starts_with("?") {
        return DanglingCloserKind::TernaryTail;
    }
    DanglingCloserKind::CallClose
}

fn repair_dangling_value_continuations(code: &str, original_source: &str, stage: &str) -> String {
    let mut source_declaration_heads: HashMap<String, String> = HashMap::new();
    // Also track semicolon-terminated constant value continuations (e.g. multiline `uint160 constant X =\n   123456789;`)
    let mut source_constant_heads: HashMap<String, String> = HashMap::new();
    // Also track multiline type-then-visibility declarations like `mapping(...)\n    public varName;`
    let mut source_type_heads: HashMap<String, String> = HashMap::new();
    let source_lines: Vec<&str> = original_source.lines().collect();

    for (idx, line) in source_lines.iter().enumerate() {
        let trimmed = line.trim();

        // Comma-terminated argument continuations
        if looks_like_call_argument_continuation(trimmed) {
            if let Some(head) = previous_nonempty_line(&source_lines, idx) {
                let head_trimmed = head.trim();
                if looks_like_multiline_expression_prefix(head_trimmed) {
                    source_declaration_heads
                        .entry(trimmed.to_string())
                        .or_insert_with(|| head.to_string());
                }
            }
        }

        // Semicolon-terminated numeric/literal constant value continuations
        if looks_like_semicolon_value_continuation(trimmed) {
            if let Some(head) = previous_nonempty_line(&source_lines, idx) {
                let head_trimmed = head.trim();
                if looks_like_multiline_constant_head(head_trimmed) {
                    source_constant_heads
                        .entry(trimmed.to_string())
                        .or_insert_with(|| head.to_string());
                }
            }
        }

        // Visibility+name tail of a multiline type declaration (e.g. `public queuedWithdrawal;`)
        if looks_like_visibility_name_tail(trimmed) {
            if let Some(head) = previous_nonempty_line(&source_lines, idx) {
                let head_trimmed = head.trim();
                if looks_like_multiline_type_head(head_trimmed) {
                    source_type_heads
                        .entry(trimmed.to_string())
                        .or_insert_with(|| head.to_string());
                }
            }
        }
    }

    if source_declaration_heads.is_empty()
        && source_constant_heads.is_empty()
        && source_type_heads.is_empty()
    {
        return code.to_string();
    }

    let lines: Vec<&str> = code.lines().collect();
    let mut repaired = Vec::with_capacity(lines.len());
    let mut inserted = 0usize;

    for (idx, line) in lines.iter().enumerate() {
        let trimmed = line.trim();

        // Comma-terminated continuations
        if looks_like_call_argument_continuation(trimmed)
            && !previous_output_line_is_expression_prefix(&lines, idx)
        {
            if let Some(head) = source_declaration_heads.get(trimmed) {
                repaired.push(head.clone());
                inserted += 1;
            }
        }

        // Semicolon-terminated constant value continuations
        if looks_like_semicolon_value_continuation(trimmed)
            && !previous_output_line_is_constant_head(&lines, idx)
        {
            if let Some(head) = source_constant_heads.get(trimmed) {
                repaired.push(head.clone());
                inserted += 1;
            }
        }

        // Visibility+name tail of a multiline type declaration
        if looks_like_visibility_name_tail(trimmed)
            && !previous_output_line_is_type_head(&lines, idx)
        {
            if let Some(head) = source_type_heads.get(trimmed) {
                repaired.push(head.clone());
                inserted += 1;
            }
        }

        repaired.push((*line).to_string());
    }

    if inserted > 0 {
        println!(
            "    -> Restored {} multiline declaration heads during {}.",
            inserted, stage
        );
    }

    repaired.join("\n")
}

/// Returns true for lines like `1461446703485210103287273052203988822378723970342;`
/// that look like the value half of a multiline constant declaration.
fn looks_like_semicolon_value_continuation(trimmed: &str) -> bool {
    if !trimmed.ends_with(';') || trimmed.contains('=') || trimmed.contains('{') {
        return false;
    }
    let first = trimmed.chars().next().unwrap_or_default();
    first.is_ascii_digit()
        || trimmed.starts_with("0x")
        || trimmed.starts_with("-")
        || trimmed.starts_with('"')
        || trimmed.starts_with('\'')
        || trimmed.starts_with("address(")
        || trimmed.starts_with("bytes")
}

/// Returns true for lines like `uint160 internal constant MAX_V4POOL_SQRT_RATIO =`
/// i.e. a state variable / constant declaration whose value continues on the next line.
fn looks_like_multiline_constant_head(trimmed: &str) -> bool {
    trimmed.ends_with('=')
        && (trimmed.contains(" constant ")
            || trimmed.contains(" immutable ")
            || trimmed.contains(" public ")
            || trimmed.contains(" internal ")
            || trimmed.contains(" private ")
            || trimmed.contains(" external "))
        && !trimmed.starts_with("if ")
        && !trimmed.starts_with("while ")
        && !trimmed.starts_with("for ")
}

fn previous_output_line_is_constant_head(lines: &[&str], idx: usize) -> bool {
    lines[..idx]
        .iter()
        .rev()
        .find(|l| !l.trim().is_empty())
        .map(|l| looks_like_multiline_constant_head(l.trim()))
        .unwrap_or(false)
}

/// Returns true for lines like `    public queuedWithdrawal;` or `    internal _fees;`
/// that are the trailing visibility+name part of a multiline type declaration.
fn looks_like_visibility_name_tail(trimmed: &str) -> bool {
    if !trimmed.ends_with(';') || trimmed.contains('(') || trimmed.contains('=') {
        return false;
    }
    trimmed.starts_with("public ")
        || trimmed.starts_with("internal ")
        || trimmed.starts_with("private ")
        || trimmed.starts_with("external ")
        || trimmed.starts_with("override ")
        || trimmed.starts_with("virtual ")
}

/// Returns true for lines like `mapping(address => mapping(...))` or `SomeType[]`
/// that end with `)` or `]` (no semicolon, no `=`) and could be the type head
/// of a multiline variable declaration.
fn looks_like_multiline_type_head(trimmed: &str) -> bool {
    if trimmed.is_empty()
        || trimmed.ends_with(';')
        || trimmed.ends_with('=')
        || trimmed.ends_with(',')
        || trimmed.starts_with("//")
        || trimmed.starts_with("function ")
        || trimmed.starts_with("if ")
        || trimmed.starts_with("for ")
        || trimmed.starts_with("while ")
        || trimmed.starts_with("return ")
    {
        return false;
    }
    // The head must be a type expression: ends with `)`, `]`, or a type name
    (trimmed.ends_with(')') || trimmed.ends_with(']') || trimmed.ends_with('>'))
        && (trimmed.starts_with("mapping(") || trimmed.contains(" => ") || trimmed.ends_with(')'))
}

fn previous_output_line_is_type_head(lines: &[&str], idx: usize) -> bool {
    lines[..idx]
        .iter()
        .rev()
        .find(|l| !l.trim().is_empty())
        .map(|l| looks_like_multiline_type_head(l.trim()))
        .unwrap_or(false)
}

fn repair_orphan_multiline_expression_prefixes(
    code: &str,
    original_source: &str,
    stage: &str,
) -> String {
    let mut source_prefixes_by_context: HashMap<String, String> = HashMap::new();
    let mut source_prefixes_by_line: HashMap<String, String> = HashMap::new();
    let source_lines: Vec<&str> = original_source.lines().collect();

    for (idx, line) in source_lines.iter().enumerate() {
        let trimmed = line.trim();
        if !looks_like_multiline_expression_continuation(trimmed) {
            continue;
        }

        let Some(prefix) = previous_nonempty_line(&source_lines, idx) else {
            continue;
        };
        if !looks_like_multiline_expression_prefix(prefix.trim()) {
            continue;
        }

        source_prefixes_by_line
            .entry(trimmed.to_string())
            .or_insert_with(|| prefix.to_string());

        let context_key =
            expression_continuation_context_key(trimmed, next_nonempty_line(&source_lines, idx));
        source_prefixes_by_context
            .entry(context_key)
            .or_insert_with(|| prefix.to_string());
    }

    if source_prefixes_by_line.is_empty() {
        return code.to_string();
    }

    let lines: Vec<&str> = code.lines().collect();
    let mut repaired = Vec::with_capacity(lines.len());
    let mut inserted = 0usize;

    for (idx, line) in lines.iter().enumerate() {
        let trimmed = line.trim();
        if looks_like_multiline_expression_continuation(trimmed)
            && !previous_output_line_is_expression_prefix(&lines, idx)
            && !is_inside_disallowed_multiline_call_head_context(&lines, idx)
        {
            let context_key =
                expression_continuation_context_key(trimmed, next_nonempty_line(&lines, idx));
            let prefix = source_prefixes_by_context
                .get(&context_key)
                .or_else(|| source_prefixes_by_line.get(trimmed));

            if let Some(prefix) = prefix {
                repaired.push(prefix.clone());
                inserted += 1;
            }
        }
        repaired.push((*line).to_string());
    }

    if inserted > 0 {
        println!(
            "    -> Restored {} multiline expression prefixes during {}.",
            inserted, stage
        );
    }

    repaired.join("\n")
}

fn repair_corrupted_containers_from_source(
    code: &str,
    original_source: &str,
    stage: &str,
) -> String {
    let lines: Vec<&str> = code.lines().collect();
    let mut replacements: Vec<(usize, usize, String)> = Vec::new();

    for (idx, line) in lines.iter().enumerate() {
        if !is_dangling_closing_call(line.trim()) || !previous_line_opens_call(&lines, idx) {
            continue;
        }

        let Some(container_start) = find_enclosing_container_start(&lines, idx + 1) else {
            continue;
        };
        let Some(container_end) = find_block_end(&lines, container_start) else {
            continue;
        };
        let Some(container_name) = parse_container_name(lines[container_start].trim_start()) else {
            continue;
        };
        let Some(original_container) =
            extract_container_from_source(original_source, &container_name)
        else {
            continue;
        };

        replacements.push((container_start, container_end, original_container));
    }

    if replacements.is_empty() {
        return code.to_string();
    }

    replacements.sort_by_key(|(start, _, _)| *start);
    let mut deduped: Vec<(usize, usize, String)> = Vec::new();
    for replacement in replacements {
        if deduped
            .last()
            .map(|(_, end, _)| replacement.0 <= *end)
            .unwrap_or(false)
        {
            continue;
        }
        deduped.push(replacement);
    }

    let mut out = Vec::new();
    let mut cursor = 0usize;
    for (start, end, replacement) in &deduped {
        for line in lines.iter().take(*start).skip(cursor) {
            out.push((*line).to_string());
        }
        out.push(replacement.clone());
        cursor = end + 1;
    }
    for line in lines.iter().skip(cursor) {
        out.push((*line).to_string());
    }

    println!(
        "    -> Restored {} corrupted containers during {}.",
        deduped.len(),
        stage
    );

    out.join("\n")
}

fn looks_like_declaration_suffix(trimmed: &str) -> bool {
    trimmed.ends_with(';')
        && (trimmed.starts_with("public ")
            || trimmed.starts_with("private ")
            || trimmed.starts_with("internal ")
            || trimmed.starts_with("external "))
        && !trimmed.contains('(')
        && !trimmed.contains('=')
}

fn previous_line_opens_call(lines: &[&str], idx: usize) -> bool {
    previous_nonempty_line(lines, idx)
        .map(|line| line.trim_end().ends_with('('))
        .unwrap_or(false)
}

fn previous_nonempty_line<'a>(lines: &'a [&str], idx: usize) -> Option<&'a str> {
    lines[..idx]
        .iter()
        .rev()
        .copied()
        .find(|line| !line.trim().is_empty())
}

fn previous_nonempty_line_index(lines: &[&str], idx: usize) -> Option<usize> {
    (0..idx)
        .rev()
        .find(|line_idx| !lines[*line_idx].trim().is_empty())
}

fn next_nonempty_line<'a>(lines: &'a [&str], idx: usize) -> Option<&'a str> {
    lines
        .iter()
        .skip(idx + 1)
        .copied()
        .find(|line| !line.trim().is_empty())
}

fn previous_output_line_is_expression_prefix(lines: &[&str], idx: usize) -> bool {
    previous_nonempty_line(lines, idx)
        .map(|line| looks_like_multiline_expression_prefix(line.trim()))
        .unwrap_or(false)
}

fn looks_like_call_argument_continuation(trimmed: &str) -> bool {
    if !trimmed.ends_with(',') || trimmed.contains('{') || trimmed.contains(';') {
        return false;
    }

    if trimmed.starts_with("//")
        || trimmed.starts_with('*')
        || trimmed.starts_with("function ")
        || trimmed.starts_with("event ")
        || trimmed.starts_with("error ")
        || trimmed.starts_with("returns ")
        || trimmed.starts_with("return ")
    {
        return false;
    }

    let first = trimmed.chars().next().unwrap_or_default();
    first.is_ascii_alphanumeric()
        || first == '_'
        || first == '"'
        || first == '\''
        || first == '('
        || trimmed.starts_with("address(")
        || trimmed.starts_with("bytes")
}

fn looks_like_multiline_expression_continuation(trimmed: &str) -> bool {
    if trimmed.is_empty()
        || trimmed.starts_with("//")
        || trimmed.starts_with('*')
        || trimmed.starts_with("function ")
        || trimmed.starts_with("event ")
        || trimmed.starts_with("error ")
        || trimmed.starts_with("returns ")
        || trimmed.starts_with("return ")
        || trimmed.starts_with(")")
        || trimmed.starts_with("}")
        || trimmed.ends_with(',')
    {
        return false;
    }

    let operator_prefixes = [
        "&&", "||", "==", "!=", ">=", "<=", ">", "<", "+", "-", "*", "/", "%", "&", "|", "^",
    ];
    operator_prefixes
        .iter()
        .any(|prefix| trimmed.starts_with(prefix))
        || trimmed.starts_with('.')
        || trimmed.starts_with("?.")
}

fn looks_like_multiline_expression_prefix(trimmed: &str) -> bool {
    if trimmed.is_empty()
        || trimmed.starts_with("//")
        || trimmed.starts_with('*')
        || trimmed.ends_with(';')
        || trimmed.ends_with('{')
        || trimmed.ends_with('}')
    {
        return false;
    }

    let tail_operators = [
        "&&", "||", "==", "!=", ">=", "<=", ">", "<", "+", "-", "*", "/", "%", "&", "|", "^", "?",
        ":",
    ];
    tail_operators
        .iter()
        .any(|operator| trimmed.ends_with(operator))
        || trimmed.ends_with('(')
        || trimmed.ends_with('[')
        || trimmed.ends_with(',')
        || trimmed.contains('=')
        || trimmed.starts_with("return ")
}

fn is_inside_disallowed_multiline_call_head_context(lines: &[&str], idx: usize) -> bool {
    let lower_bound = idx.saturating_sub(40);
    let mut close_balance = 0i32;

    for line_idx in (lower_bound..idx).rev() {
        let trimmed = lines[line_idx].trim();
        close_balance += trimmed.matches(')').count() as i32;

        let open_count = trimmed.matches('(').count() as i32;
        if open_count > close_balance {
            return starts_disallowed_multiline_context(trimmed);
        }
        close_balance -= open_count;
        if trimmed.ends_with(';') || trimmed.ends_with('{') || trimmed.ends_with('}') {
            break;
        }
    }

    false
}

fn starts_disallowed_multiline_context(trimmed: &str) -> bool {
    let prefixes = [
        "return ",
        "return(",
        "returns ",
        "function ",
        "event ",
        "error ",
        "modifier ",
        "if ",
        "while ",
        "for ",
        "catch ",
    ];
    prefixes.iter().any(|prefix| trimmed.starts_with(prefix))
}

fn expression_continuation_context_key(trimmed: &str, next: Option<&str>) -> String {
    format!("{}\n{}", trimmed, next.map(str::trim).unwrap_or(""))
}

fn compiler_error_from_text(text: &str) -> Option<CompilerError> {
    let first = text.lines().next()?.trim();
    let category = if first.starts_with("Syntax") || first.to_lowercase().contains("expected") {
        CompilerErrorCategory::Syntax
    } else {
        CompilerErrorCategory::Other
    };
    let code = first
        .split_once('(')
        .and_then(|(_, rest)| rest.split_once(')'))
        .map(|(code, _)| code.to_string());
    let message = first
        .split_once(": ")
        .map(|(_, message)| message.to_string())
        .unwrap_or_else(|| first.to_string());

    let mut line = None;
    let mut column = None;
    for part in text.split_whitespace() {
        let Some((maybe_line, maybe_column)) = part.rsplit_once(':') else {
            continue;
        };
        let Some((_, maybe_line)) = maybe_line.rsplit_once(':') else {
            continue;
        };
        if let (Ok(parsed_line), Ok(parsed_column)) =
            (maybe_line.parse::<usize>(), maybe_column.parse::<usize>())
        {
            line = Some(parsed_line);
            column = Some(parsed_column);
            break;
        }
    }
    if line.is_none() {
        for text_line in text.lines() {
            let trimmed = text_line.trim();
            let Some((maybe_line, _)) = trimmed.split_once('|') else {
                continue;
            };
            if let Ok(parsed_line) = maybe_line.trim().parse::<usize>() {
                line = Some(parsed_line);
                break;
            }
        }
    }

    Some(CompilerError {
        code,
        message,
        file: None,
        line,
        column,
        category,
        snippet: text.lines().map(str::to_string).collect(),
    })
}

fn try_batch_source_container_repair(
    code: &str,
    errors: &[CompilerError],
    source_index: &SourceIndex,
    restore_history: &RestoreHistory,
    baseline_output_lines: usize,
) -> Option<DeterministicRepair> {
    let lines: Vec<&str> = code.lines().collect();
    let mut replacements: Vec<(usize, usize, ContainerReplacement, String)> = Vec::new();
    let mut dangling_by_scope: HashMap<String, usize> = HashMap::new();

    for err in errors {
        let Some(line_no) = err.line else {
            continue;
        };
        let Some(line) = lines.get(line_no.saturating_sub(1)) else {
            continue;
        };
        if err.category != CompilerErrorCategory::Syntax || !is_dangling_closing_call(line.trim()) {
            continue;
        }
        let scope = logical_error_scope(&lines, line_no);
        *dangling_by_scope.entry(scope).or_default() += 1;
    }

    for err in errors {
        let Some(line_no) = err.line else {
            continue;
        };
        let Some(line) = lines.get(line_no.saturating_sub(1)) else {
            continue;
        };
        if err.category != CompilerErrorCategory::Syntax || !is_dangling_closing_call(line.trim()) {
            continue;
        }
        let scope = logical_error_scope(&lines, line_no);
        if dangling_by_scope.get(&scope).copied().unwrap_or(0) < 2 {
            continue;
        }
        let Some(container_start) = find_enclosing_container_start(&lines, line_no) else {
            continue;
        };
        let Some(container_end) = find_block_end(&lines, container_start) else {
            continue;
        };
        let Some(container_name) = parse_container_name(lines[container_start].trim_start()) else {
            continue;
        };
        let Some(source_container) = source_index.container(&container_name) else {
            continue;
        };
        let target = ContainerReplacement {
            container_name: container_name.clone(),
            expected_hash: source_container.body_hash,
        };
        if restore_history.has_container(&target) {
            continue;
        }
        let candidate_lines = lines.len() - (container_end - container_start + 1)
            + source_container.source.lines().count();
        if code.lines().count() > baseline_output_lines.saturating_mul(2)
            || candidate_lines > baseline_output_lines.saturating_mul(2)
        {
            continue;
        }
        if replacements
            .iter()
            .any(|(start, end, _, _)| ranges_overlap(container_start, container_end, *start, *end))
        {
            continue;
        }
        replacements.push((
            container_start,
            container_end,
            target,
            source_container.source.clone(),
        ));
    }

    if replacements.is_empty() {
        return None;
    }

    replacements.sort_by_key(|(start, _, _, _)| *start);
    let mut repaired = Vec::new();
    let mut cursor = 0usize;
    let mut container_replacements = Vec::new();
    for (start, end, target, source) in &replacements {
        for line in lines.iter().take(*start).skip(cursor) {
            repaired.push((*line).to_string());
        }
        repaired.push(source.clone());
        cursor = end + 1;
        if !container_replacements.contains(target) {
            container_replacements.push(target.clone());
        }
    }
    for line in lines.iter().skip(cursor) {
        repaired.push((*line).to_string());
    }

    println!(
        "    -> Restored {} source-backed container(s) after repeated dangling closes.",
        container_replacements.len()
    );
    Some(DeterministicRepair::source_backed_containers(
        repaired.join("\n"),
        Vec::new(),
        container_replacements,
    ))
}

fn try_batch_source_function_repair(
    code: &str,
    errors: &[CompilerError],
    source_index: &SourceIndex,
    restore_history: &RestoreHistory,
    baseline_output_lines: usize,
    validation_target: Option<&HarnessValidationTarget>,
) -> Option<DeterministicRepair> {
    let lines: Vec<&str> = code.lines().collect();
    let mut replacements: Vec<(usize, usize, SourceReplacement, String)> = Vec::new();
    let mut source_backed_containers = HashSet::new();

    for err in errors {
        if !should_recover_function_from_source(err) {
            continue;
        }
        let Some(line_no) = err.line else {
            continue;
        };
        if error_line_is_protected_target_or_setup_function(&lines, line_no, validation_target) {
            continue;
        }
        let Some((start, end, target, source)) =
            source_function_replacement_for_line(&lines, line_no, source_index)
        else {
            continue;
        };
        if restore_history.has_function(&target) {
            continue;
        }
        if let Some(container_name) = target.container_name.as_ref() {
            source_backed_containers.insert(container_name.clone());
        }

        let current_function = lines[start..=end].join("\n");
        if !source_function_is_better(&source, &current_function) {
            continue;
        }

        if replacements
            .iter()
            .any(|(existing_start, existing_end, _, _)| {
                ranges_overlap(start, end, *existing_start, *existing_end)
            })
        {
            continue;
        }

        replacements.push((start, end, target, source));
    }

    if let Some(repair) = try_source_container_repair_for_corrupted_siblings(
        &lines,
        &source_backed_containers,
        source_index,
        restore_history,
        baseline_output_lines,
    ) {
        return Some(repair);
    }

    if replacements.is_empty() {
        return None;
    }

    replacements.sort_by_key(|(start, _, _, _)| *start);
    let mut repaired = Vec::new();
    let mut cursor = 0usize;
    let mut source_replacements = Vec::new();
    for (start, end, target, source) in &replacements {
        for line in lines.iter().take(*start).skip(cursor) {
            repaired.push((*line).to_string());
        }
        repaired.push(source.clone());
        cursor = end + 1;
        if !source_replacements.contains(target) {
            source_replacements.push(target.clone());
        }
    }
    for line in lines.iter().skip(cursor) {
        repaired.push((*line).to_string());
    }

    println!(
        "    -> Restored {} source-backed function(s) in one deterministic batch.",
        replacements.len()
    );
    crate::execution_log::detail(
        "resurrection_source_backed_batch",
        format!("functions={}", replacements.len()),
    );

    Some(DeterministicRepair::source_backed(
        repaired.join("\n"),
        source_replacements,
    ))
}

fn try_syntax_error_guided_source_restore(
    code: &str,
    errors: &[CompilerError],
    source_index: &SourceIndex,
    protected_functions: &[SourceReplacement],
    protected_containers: &[ContainerReplacement],
    restore_history: &RestoreHistory,
    baseline_output_lines: usize,
    validation_target: Option<&HarnessValidationTarget>,
) -> Option<DeterministicRepair> {
    let lines: Vec<&str> = code.lines().collect();
    let provenance =
        OutputLineProvenanceMap::build(code, &[], protected_functions, protected_containers);
    let mut syntax_errors = Vec::new();
    let mut container_counts: HashMap<String, usize> = HashMap::new();

    for err in errors {
        let Some(line_no) = err.line else {
            continue;
        };
        let Some(line) = lines.get(line_no.saturating_sub(1)) else {
            continue;
        };
        if !is_structural_syntax_error(err, line.trim()) {
            continue;
        }
        let Some(prov) = provenance.get(line_no) else {
            continue;
        };
        if let Some(container) = prov.container.as_ref() {
            *container_counts.entry(container.clone()).or_default() += 1;
        }
        syntax_errors.push((err, line_no, prov.clone()));
    }

    if syntax_errors.is_empty() {
        return None;
    }

    for (container_name, count) in &container_counts {
        if *count < 4 {
            continue;
        }
        if validation_target
            .map(|target| target.match_contract == *container_name)
            .unwrap_or(false)
        {
            continue;
        }
        let Some((container_start, container_end)) =
            current_container_span_by_name(&lines, container_name)
        else {
            continue;
        };
        let Some(source_container) = source_index.container(container_name) else {
            continue;
        };
        let target = ContainerReplacement {
            container_name: container_name.clone(),
            expected_hash: source_container.body_hash,
        };
        if restore_history.has_container(&target) || protected_containers.contains(&target) {
            continue;
        }
        let mut repaired = Vec::new();
        for line in lines.iter().take(container_start) {
            repaired.push((*line).to_string());
        }
        repaired.push(source_container.source.clone());
        for line in lines.iter().skip(container_end + 1) {
            repaired.push((*line).to_string());
        }
        let repaired_code = repaired.join("\n");
        if code.lines().count() > baseline_output_lines.saturating_mul(2)
            || repaired_code.lines().count() > baseline_output_lines.saturating_mul(2)
        {
            println!(
                "    -> Skipped syntax-guided container restore for {}: line budget exceeded.",
                container_name
            );
            crate::execution_log::detail(
                "syntax_guided_source_restore_skipped",
                format!(
                    "kind=container container={} reason=line_budget baseline={}",
                    container_name, baseline_output_lines
                ),
            );
            continue;
        }
        println!(
            "    -> Syntax-guided restore escalated to full container {} after {} syntax errors.",
            container_name, count
        );
        crate::execution_log::detail(
            "syntax_guided_source_restore",
            format!(
                "kind=container container={} syntax_errors={}",
                container_name, count
            ),
        );
        return Some(DeterministicRepair::source_backed_containers(
            repaired_code,
            Vec::new(),
            vec![target],
        ));
    }

    let mut replacements: Vec<(usize, usize, SourceReplacement, String)> = Vec::new();
    for (_err, line_no, prov) in syntax_errors {
        if matches!(
            prov.restore_kind,
            RestoreKind::SourceBackedFunction | RestoreKind::SourceBackedContainer
        ) {
            continue;
        }
        if is_protected_target_or_setup_function(
            prov.container.as_deref(),
            prov.function.as_deref(),
            validation_target,
        ) {
            continue;
        }

        let Some(function_name) = prov.function.as_ref() else {
            continue;
        };
        let Some(function_start) = find_enclosing_function_start(&lines, line_no) else {
            continue;
        };
        let Some(function_end) = find_function_end(&lines, function_start) else {
            continue;
        };
        if line_no.saturating_sub(1) > function_end {
            continue;
        }
        let Some(source_function) =
            source_index.function(prov.container.as_deref(), function_name, prov.param_count)
        else {
            continue;
        };
        let target = SourceReplacement {
            container_name: prov.container.clone(),
            function_name: function_name.clone(),
            param_count: prov.param_count,
            expected_hash: source_function.body_hash,
        };
        if protected_functions.contains(&target) {
            continue;
        }
        if restore_history.has_function(&target) {
            continue;
        }
        if replacements
            .iter()
            .any(|(existing_start, existing_end, _, _)| {
                ranges_overlap(function_start, function_end, *existing_start, *existing_end)
            })
        {
            continue;
        }
        replacements.push((
            function_start,
            function_end,
            target,
            source_function.source.clone(),
        ));
    }

    if replacements.is_empty() {
        return None;
    }

    replacements.sort_by_key(|(start, _, _, _)| *start);
    let mut repaired = Vec::new();
    let mut cursor = 0usize;
    let mut source_replacements = Vec::new();
    for (start, end, target, source) in &replacements {
        for line in lines.iter().take(*start).skip(cursor) {
            repaired.push((*line).to_string());
        }
        repaired.push(source.clone());
        cursor = end + 1;
        if !source_replacements.contains(target) {
            source_replacements.push(target.clone());
        }
    }
    for line in lines.iter().skip(cursor) {
        repaired.push((*line).to_string());
    }

    println!(
        "    -> Syntax-guided source restore replaced {} function(s).",
        source_replacements.len()
    );
    crate::execution_log::detail(
        "syntax_guided_source_restore",
        format!(
            "kind=function functions={}",
            source_replacements
                .iter()
                .map(|replacement| match replacement.container_name.as_ref() {
                    Some(container) => format!("{}::{}", container, replacement.function_name),
                    None => replacement.function_name.clone(),
                })
                .collect::<Vec<_>>()
                .join(",")
        ),
    );

    Some(DeterministicRepair::source_backed(
        repaired.join("\n"),
        source_replacements,
    ))
}

fn try_source_container_repair_for_corrupted_siblings(
    lines: &[&str],
    container_names: &HashSet<String>,
    source_index: &SourceIndex,
    restore_history: &RestoreHistory,
    baseline_output_lines: usize,
) -> Option<DeterministicRepair> {
    let mut replacements: Vec<(usize, usize, ContainerReplacement, String)> = Vec::new();
    let mut ordered_container_names: Vec<&String> = container_names.iter().collect();
    ordered_container_names.sort();

    for container_name in ordered_container_names {
        let Some((container_start, container_end)) =
            current_container_span_by_name(lines, container_name)
        else {
            continue;
        };
        let corrupted_count = corrupted_source_backed_function_count(
            lines,
            container_start,
            container_end,
            container_name,
            source_index,
        );
        if corrupted_count < 2 {
            continue;
        }
        let Some(source_container) = source_index.container(container_name) else {
            continue;
        };
        let target = ContainerReplacement {
            container_name: container_name.clone(),
            expected_hash: source_container.body_hash,
        };
        if restore_history.has_container(&target) {
            continue;
        }
        let candidate_lines = lines.len() - (container_end - container_start + 1)
            + source_container.source.lines().count();
        if lines.len() > baseline_output_lines.saturating_mul(2)
            || candidate_lines > baseline_output_lines.saturating_mul(2)
        {
            continue;
        }
        if replacements
            .iter()
            .any(|(start, end, _, _)| ranges_overlap(container_start, container_end, *start, *end))
        {
            continue;
        }
        replacements.push((
            container_start,
            container_end,
            target,
            source_container.source.clone(),
        ));
    }

    if replacements.is_empty() {
        return None;
    }

    replacements.sort_by_key(|(start, _, _, _)| *start);
    let mut repaired = Vec::new();
    let mut cursor = 0usize;
    let mut container_replacements = Vec::new();
    for (start, end, target, source) in &replacements {
        for line in lines.iter().take(*start).skip(cursor) {
            repaired.push((*line).to_string());
        }
        repaired.push(source.clone());
        cursor = end + 1;
        if !container_replacements.contains(target) {
            container_replacements.push(target.clone());
        }
    }
    for line in lines.iter().skip(cursor) {
        repaired.push((*line).to_string());
    }

    println!(
        "    -> Restored {} source-backed container(s) with multiple corrupted functions.",
        container_replacements.len()
    );
    crate::execution_log::detail(
        "resurrection_source_backed_container_batch",
        format!("containers={}", container_replacements.len()),
    );

    Some(DeterministicRepair::source_backed_containers(
        repaired.join("\n"),
        Vec::new(),
        container_replacements,
    ))
}

fn current_container_span_by_name(lines: &[&str], container_name: &str) -> Option<(usize, usize)> {
    for (idx, line) in lines.iter().enumerate() {
        let trimmed = line.trim_start();
        let Some(name) = parse_container_name(trimmed) else {
            continue;
        };
        if name != container_name {
            continue;
        }
        let end = find_block_end(lines, idx)?;
        return Some((idx, end));
    }
    None
}

fn corrupted_source_backed_function_count(
    lines: &[&str],
    container_start: usize,
    container_end: usize,
    container_name: &str,
    source_index: &SourceIndex,
) -> usize {
    let mut count = 0usize;
    let mut idx = container_start + 1;
    let source_function_count = source_index.functions_in_container(container_name).len();
    if source_function_count == 0 {
        return 0;
    }

    while idx < container_end {
        let trimmed = lines[idx].trim_start();
        if !trimmed.starts_with("function ") {
            idx += 1;
            continue;
        }

        let Some(function_name) = parse_function_name(trimmed) else {
            idx += 1;
            continue;
        };
        let Some(function_end) = find_function_end(lines, idx) else {
            idx += 1;
            continue;
        };
        let param_count = function_param_count_from_lines(lines, idx);
        if let Some(source_function) =
            source_index.function(Some(container_name), &function_name, param_count)
        {
            let current_function = lines[idx..=function_end].join("\n");
            if source_function_is_obviously_corrupted(&source_function.source, &current_function) {
                count += 1;
            }
        }
        idx = function_end + 1;
    }

    count
}

fn should_recover_function_from_source(err: &CompilerError) -> bool {
    err.category == CompilerErrorCategory::Syntax
        && (looks_like_parser_error(err)
            || err.message.contains("Expected primary expression")
            || err.message.contains("Expected ';'"))
}

fn source_function_replacement_for_line(
    lines: &[&str],
    line_no: usize,
    source_index: &SourceIndex,
) -> Option<(usize, usize, SourceReplacement, String)> {
    let function_start = find_enclosing_function_start(lines, line_no)?;
    let function_end = find_function_end(lines, function_start)?;
    if line_no.saturating_sub(1) > function_end {
        return None;
    }

    let function_name = parse_function_name(lines.get(function_start)?.trim_start())?;
    let container_name = find_enclosing_container_start(lines, function_start + 1)
        .and_then(|idx| parse_container_name(lines.get(idx)?.trim_start()));
    let param_count = function_param_count_from_lines(lines, function_start);
    let source_function =
        source_index.function(container_name.as_deref(), &function_name, param_count)?;

    let target = SourceReplacement {
        container_name,
        function_name,
        param_count,
        expected_hash: source_function.body_hash,
    };

    Some((
        function_start,
        function_end,
        target,
        source_function.source.clone(),
    ))
}

fn protect_source_replacements(
    code: &str,
    replacements: &[SourceReplacement],
    container_replacements: &[ContainerReplacement],
    source_index: &SourceIndex,
) -> String {
    let mut protected = code.to_string();
    for replacement in replacements {
        if let Some(next) = replace_function_by_source_target(&protected, replacement, source_index)
        {
            protected = next;
        }
    }
    for replacement in container_replacements {
        if let Some(next) =
            replace_container_by_source_target(&protected, replacement, source_index)
        {
            protected = next;
        }
    }
    protected
}

fn protect_replacements(
    code: &str,
    statement_replacements: &[StatementReplacement],
    replacements: &[SourceReplacement],
    container_replacements: &[ContainerReplacement],
    source_index: &SourceIndex,
) -> String {
    let mut protected =
        protect_source_replacements(code, replacements, container_replacements, source_index);
    for replacement in statement_replacements {
        if let Some(next) = replace_statement_by_source_target(&protected, replacement) {
            protected = next;
        }
    }
    protected
}

fn replace_statement_by_source_target(code: &str, target: &StatementReplacement) -> Option<String> {
    let lines: Vec<&str> = code.lines().collect();
    let function_start = lines.iter().enumerate().find_map(|(idx, line)| {
        let trimmed = line.trim_start();
        if !trimmed.starts_with("function ")
            || parse_function_name(trimmed).as_deref() != Some(target.function_name.as_str())
        {
            return None;
        }
        let container_name = find_enclosing_container_start(&lines, idx + 1)
            .and_then(|container_idx| parse_container_name(lines.get(container_idx)?.trim_start()));
        if target.container_name.as_deref() != container_name.as_deref() {
            return None;
        }
        if target.param_count.is_some()
            && function_param_count_from_lines(&lines, idx) != target.param_count
        {
            return None;
        }
        Some(idx)
    })?;
    let function_end = find_function_end(&lines, function_start)?;
    let function_text = lines[function_start..=function_end].join("\n");
    if function_text.contains(target.source_text.trim()) {
        return None;
    }

    let source_tokens = identifiers_in_line(&target.source_text);
    let mut best: Option<(usize, usize, usize)> = None;
    for idx in function_start..=function_end {
        let span = find_statement_span(&lines, idx, function_start, function_end);
        let statement = lines[span.0..=span.1].join("\n");
        let score = statement_similarity_score(&statement, &target.source_text, &source_tokens);
        if score == 0 {
            continue;
        }
        if best
            .map(|(_, _, best_score)| score > best_score)
            .unwrap_or(true)
        {
            best = Some((span.0, span.1, score));
        }
    }

    let (start, end, _) = best?;
    let current_statement = lines[start..=end].join("\n");
    if stable_hash(&current_statement) == target.expected_hash {
        return None;
    }

    let mut repaired = Vec::new();
    for line in lines.iter().take(start) {
        repaired.push((*line).to_string());
    }
    repaired.push(target.source_text.clone());
    for line in lines.iter().skip(end + 1) {
        repaired.push((*line).to_string());
    }
    println!(
        "    -> Re-applied protected target statement in {} after cleanup.",
        target.function_name
    );
    Some(repaired.join("\n"))
}

fn replace_function_by_source_target(
    code: &str,
    target: &SourceReplacement,
    source_index: &SourceIndex,
) -> Option<String> {
    let lines: Vec<&str> = code.lines().collect();
    let source_function = source_index.function(
        target.container_name.as_deref(),
        &target.function_name,
        target.param_count,
    )?;
    if source_function.body_hash != target.expected_hash {
        return None;
    }
    let source = source_function.source.clone();

    for (idx, line) in lines.iter().enumerate() {
        let trimmed = line.trim_start();
        if !trimmed.starts_with("function ")
            || parse_function_name(trimmed).as_deref() != Some(target.function_name.as_str())
        {
            continue;
        }

        let container_name = find_enclosing_container_start(&lines, idx + 1)
            .and_then(|container_idx| parse_container_name(lines.get(container_idx)?.trim_start()));
        if target.container_name.as_deref() != container_name.as_deref() {
            continue;
        }
        if target.param_count.is_some()
            && function_param_count_from_lines(&lines, idx) != target.param_count
        {
            continue;
        }

        let end = find_function_end(&lines, idx)?;
        let current = lines[idx..=end].join("\n");
        if stable_hash(&current) == stable_hash(&source) {
            return None;
        }

        let mut repaired = Vec::new();
        for line in lines.iter().take(idx) {
            repaired.push((*line).to_string());
        }
        repaired.push(source);
        for line in lines.iter().skip(end + 1) {
            repaired.push((*line).to_string());
        }
        println!(
            "    -> Re-applied protected source function {} after heuristic cleanup.",
            target.function_name
        );
        return Some(repaired.join("\n"));
    }

    None
}

fn replace_container_by_source_target(
    code: &str,
    target: &ContainerReplacement,
    source_index: &SourceIndex,
) -> Option<String> {
    let source_container = source_index.container(&target.container_name)?;
    if source_container.body_hash != target.expected_hash {
        return None;
    }
    replace_top_level_definition_by_name(code, &target.container_name, &source_container.source)
}

fn source_function_is_better(source: &str, current: &str) -> bool {
    if source.trim() == current.trim() {
        return false;
    }

    let source_score = expression_balance_score(source);
    let current_score = expression_balance_score(current);
    source_score <= current_score
        || current
            .lines()
            .any(|line| is_dangling_closing_call(line.trim()))
        || meaningful_line_count(source) > meaningful_line_count(current)
}

fn source_function_is_obviously_corrupted(source: &str, current: &str) -> bool {
    if source.trim() == current.trim() {
        return false;
    }

    current
        .lines()
        .any(|line| is_dangling_closing_call(line.trim()))
        || has_empty_multiline_call(current)
        || (source_contains_return(source) && !source_contains_return(current))
        || expression_balance_score(current) > expression_balance_score(source)
}

fn has_empty_multiline_call(code: &str) -> bool {
    let lines: Vec<&str> = code.lines().collect();
    for (idx, line) in lines.iter().enumerate() {
        let trimmed = line.trim();
        if !trimmed.ends_with('(') {
            continue;
        }
        if next_nonempty_line(&lines, idx + 1)
            .map(|next| next.trim() == ");")
            .unwrap_or(false)
        {
            return true;
        }
    }
    false
}

fn source_contains_return(code: &str) -> bool {
    code.lines().any(|line| {
        let trimmed = line.trim_start();
        trimmed == "return;" || trimmed.starts_with("return ")
    })
}

fn meaningful_line_count(code: &str) -> usize {
    code.lines()
        .map(str::trim)
        .filter(|line| !line.is_empty() && !line.starts_with("//") && !line.starts_with('*'))
        .count()
}

fn expression_balance_score(code: &str) -> usize {
    let mut paren = 0i32;
    let mut bracket = 0i32;
    let mut negative = 0usize;
    let mut in_multi_line_comment = false;

    for line in code.lines() {
        let mut in_single_quote = false;
        let mut in_double_quote = false;
        let mut chars = line.chars().peekable();
        while let Some(ch) = chars.next() {
            if in_multi_line_comment {
                if ch == '*' && chars.peek() == Some(&'/') {
                    chars.next();
                    in_multi_line_comment = false;
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
                    in_multi_line_comment = true;
                }
                '\'' => in_single_quote = true,
                '"' => in_double_quote = true,
                '(' => paren += 1,
                ')' => {
                    paren -= 1;
                    if paren < 0 {
                        negative += 1;
                        paren = 0;
                    }
                }
                '[' => bracket += 1,
                ']' => {
                    bracket -= 1;
                    if bracket < 0 {
                        negative += 1;
                        bracket = 0;
                    }
                }
                _ => {}
            }
        }
    }

    negative + paren.unsigned_abs() as usize + bracket.unsigned_abs() as usize
}

fn ranges_overlap(a_start: usize, a_end: usize, b_start: usize, b_end: usize) -> bool {
    a_start <= b_end && b_start <= a_end
}

fn try_statement_span_source_repair(
    code: &str,
    errors: &[CompilerError],
    source_index: &SourceIndex,
) -> Option<DeterministicRepair> {
    let lines: Vec<&str> = code.lines().collect();
    for err in errors {
        if err.category != CompilerErrorCategory::Syntax || !looks_like_parser_error(err) {
            continue;
        }
        let Some(line_no) = err.line else {
            continue;
        };
        let Some(line) = lines.get(line_no.saturating_sub(1)) else {
            continue;
        };
        let trimmed = line.trim();
        if !(is_statement_fragment(trimmed)
            || looks_like_call_argument_continuation(trimmed)
            || looks_like_multiline_expression_continuation(trimmed)
            || looks_like_declaration_suffix(trimmed))
        {
            continue;
        }
        let Some(function_start) = find_enclosing_function_start(&lines, line_no) else {
            continue;
        };
        let Some(function_end) = find_function_end(&lines, function_start) else {
            continue;
        };
        let function_name = parse_function_name(lines[function_start].trim_start())?;
        let container_name = find_enclosing_container_start(&lines, function_start + 1)
            .and_then(|idx| parse_container_name(lines[idx].trim_start()));
        let param_count = function_param_count_from_lines(&lines, function_start);
        let source_function =
            source_index.function(container_name.as_deref(), &function_name, param_count)?;
        let source_lines: Vec<&str> = source_function.source.lines().collect();
        let broken_stmt = find_statement_span(
            &lines,
            line_no.saturating_sub(1),
            function_start,
            function_end,
        );
        let Some(source_stmt) = match_statement_in_source(trimmed, &source_lines) else {
            continue;
        };
        if lines[broken_stmt.0..=broken_stmt.1].join("\n").trim() == source_stmt.trim() {
            continue;
        }
        let mut repaired = Vec::new();
        for line in lines.iter().take(broken_stmt.0) {
            repaired.push((*line).to_string());
        }
        repaired.push(source_stmt);
        for line in lines.iter().skip(broken_stmt.1 + 1) {
            repaired.push((*line).to_string());
        }
        println!(
            "    -> Restored source-backed statement span in {}.",
            function_name
        );
        crate::execution_log::detail(
            "resurrection_statement_span_repair",
            format!(
                "container={} function={} lines={}..{} source_hash={}",
                container_name.as_deref().unwrap_or("<none>"),
                function_name,
                broken_stmt.0 + 1,
                broken_stmt.1 + 1,
                source_function.body_hash
            ),
        );
        return Some(DeterministicRepair::source_backed(
            repaired.join("\n"),
            vec![SourceReplacement {
                container_name,
                function_name,
                param_count,
                expected_hash: source_function.body_hash,
            }],
        ));
    }
    None
}

fn try_target_statement_restore(
    code: &str,
    errors: &[CompilerError],
    source_index: &SourceIndex,
    protected_statements: &[StatementReplacement],
    restore_history: &RestoreHistory,
    baseline_output_lines: usize,
    validation_target: Option<&HarnessValidationTarget>,
) -> Option<DeterministicRepair> {
    let target = validation_target?;
    let lines: Vec<&str> = code.lines().collect();

    for err in errors {
        let Some(line_no) = err.line else {
            continue;
        };
        let Some(line) = lines.get(line_no.saturating_sub(1)) else {
            continue;
        };
        if !is_structural_syntax_error(err, line.trim()) {
            continue;
        }
        if !error_line_is_exact_target_function(&lines, line_no, target) {
            continue;
        }

        let Some(function_start) = find_enclosing_function_start(&lines, line_no) else {
            continue;
        };
        let Some(function_end) = find_function_end(&lines, function_start) else {
            continue;
        };
        let param_count = function_param_count_from_lines(&lines, function_start);
        let Some(source_function) = source_index.function(
            Some(target.match_contract.as_str()),
            target.match_test.as_str(),
            param_count,
        ) else {
            log_unresolved_target_statement_slice(target, line_no, "no_source_function");
            continue;
        };

        let broken_span = find_target_statement_span(
            &lines,
            line_no.saturating_sub(1),
            function_start,
            function_end,
        );
        let broken_statement = lines[broken_span.0..=broken_span.1].join("\n");
        let source_lines: Vec<&str> = source_function.source.lines().collect();
        let Some(source_statement) = match_statement_in_source(&broken_statement, &source_lines)
        else {
            log_unresolved_target_statement_slice(target, line_no, "no_statement_provenance");
            continue;
        };

        let source_statement_lines = source_statement.lines().count();
        let source_function_lines = source_function.source.lines().count().max(1);
        let max_statement_lines = 20usize.max(source_function_lines * 40 / 100);
        if code.lines().count() > baseline_output_lines.saturating_mul(2)
            || source_statement_lines > max_statement_lines
        {
            log_unresolved_target_statement_slice(
                target,
                line_no,
                "statement_closure_exceeded_budget",
            );
            continue;
        }

        if broken_statement.trim() == source_statement.trim() {
            continue;
        }

        let replacement = StatementReplacement {
            container_name: Some(target.match_contract.clone()),
            function_name: target.match_test.clone(),
            param_count,
            expected_hash: stable_hash(&source_statement),
            source_text: source_statement.clone(),
            statement_hash: None,
            original_source: None,
            restored_source: None,
            reason: None,
        };
        if protected_statements.contains(&replacement)
            || restore_history.has_statement(&replacement)
        {
            log_unresolved_target_statement_slice(target, line_no, "statement_already_restored");
            continue;
        }

        let mut repaired = Vec::new();
        for line in lines.iter().take(broken_span.0) {
            repaired.push((*line).to_string());
        }
        repaired.push(source_statement);
        for line in lines.iter().skip(broken_span.1 + 1) {
            repaired.push((*line).to_string());
        }

        println!(
            "    -> Restored target statement span in {}::{}.",
            target.match_contract, target.match_test
        );
        crate::execution_log::detail(
            "target_statement_restore",
            format!(
                "target={}::{} lines={}..{} source_hash={}",
                target.match_contract,
                target.match_test,
                broken_span.0 + 1,
                broken_span.1 + 1,
                replacement.expected_hash
            ),
        );
        return Some(DeterministicRepair::source_backed_statements(
            repaired.join("\n"),
            vec![replacement],
        ));
    }

    None
}

fn is_statement_fragment(trimmed: &str) -> bool {
    trimmed == ");"
        || trimmed == "}"
        || trimmed == "},"
        || trimmed == ","
        || trimmed.starts_with(");")
        || trimmed.starts_with("},")
        || trimmed.starts_with(',')
}

fn find_target_statement_span(
    lines: &[&str],
    error_idx: usize,
    function_start: usize,
    function_end: usize,
) -> (usize, usize) {
    let trimmed = lines
        .get(error_idx)
        .map(|line| line.trim())
        .unwrap_or_default();
    if is_dangling_closing_call(trimmed) {
        if let Some(call_start) = find_nearest_multiline_call_head(lines, error_idx, function_start)
        {
            return (call_start, error_idx.min(function_end));
        }
    }
    find_statement_span(lines, error_idx, function_start, function_end)
}

fn find_nearest_multiline_call_head(
    lines: &[&str],
    error_idx: usize,
    lower: usize,
) -> Option<usize> {
    for idx in (lower..error_idx).rev() {
        let trimmed = lines[idx].trim();
        if trimmed.is_empty() || trimmed.starts_with("//") {
            continue;
        }
        if trimmed.ends_with(';') || trimmed.ends_with('}') || trimmed.ends_with('{') {
            break;
        }
        if trimmed.ends_with('(') && statement_call_or_assignment_head(trimmed).is_some() {
            return Some(idx);
        }
    }
    None
}

fn is_structural_syntax_error(err: &CompilerError, trimmed_line: &str) -> bool {
    if err.category != CompilerErrorCategory::Syntax {
        return false;
    }

    let message = err.message.to_lowercase();
    let structural_message = message.contains("expected primary expression")
        || message.contains("expected ','")
        || message.contains("expected ';'")
        || message.contains("expected ':'")
        || message.contains("expected expression")
        || message.contains("unexpected token")
        || message.contains("unexpected");

    structural_message && is_typical_incomplete_syntax_line(trimmed_line)
}

fn is_typical_incomplete_syntax_line(trimmed: &str) -> bool {
    if trimmed.is_empty() {
        return false;
    }

    is_dangling_closing_call(trimmed)
        || is_statement_fragment(trimmed)
        || looks_like_call_argument_continuation(trimmed)
        || matches!(trimmed, "," | ";" | "?" | ":" | ");" | "),")
        || trimmed == "return ("
        || trimmed.starts_with("return (")
        || trimmed.ends_with('?')
        || trimmed.ends_with(':')
}

fn syntax_errors_in_restored_spans(
    code: &str,
    errors: &[CompilerError],
    statement_replacements: &[StatementReplacement],
    source_replacements: &[SourceReplacement],
    container_replacements: &[ContainerReplacement],
) -> bool {
    if statement_replacements.is_empty()
        && source_replacements.is_empty()
        && container_replacements.is_empty()
    {
        return false;
    }

    let provenance = OutputLineProvenanceMap::build(
        code,
        statement_replacements,
        source_replacements,
        container_replacements,
    );
    errors.iter().any(|err| {
        if err.category != CompilerErrorCategory::Syntax {
            return false;
        }
        let Some(line_no) = err.line else {
            return false;
        };
        let Some(prov) = provenance.get(line_no) else {
            return false;
        };

        statement_replacements
            .iter()
            .any(|replacement| error_line_matches_statement_replacement(code, line_no, replacement))
            || container_replacements.iter().any(|replacement| {
                prov.container.as_deref() == Some(replacement.container_name.as_str())
            })
            || source_replacements.iter().any(|replacement| {
                replacement.container_name.as_deref() == prov.container.as_deref()
                    && Some(replacement.function_name.as_str()) == prov.function.as_deref()
                    && replacement.param_count == prov.param_count
            })
    })
}

fn error_line_matches_statement_replacement(
    code: &str,
    line_no: usize,
    replacement: &StatementReplacement,
) -> bool {
    let lines: Vec<&str> = code.lines().collect();
    let Some(function_start) = find_enclosing_function_start(&lines, line_no) else {
        return false;
    };
    let function_name = parse_function_name(lines[function_start].trim_start());
    if function_name.as_deref() != Some(replacement.function_name.as_str()) {
        return false;
    }
    let container_name = find_enclosing_container_start(&lines, line_no)
        .and_then(|idx| parse_container_name(lines[idx].trim_start()));
    if container_name.as_deref() != replacement.container_name.as_deref() {
        return false;
    }
    if replacement.param_count.is_some()
        && function_param_count_from_lines(&lines, function_start) != replacement.param_count
    {
        return false;
    }
    let Some(function_end) = find_function_end(&lines, function_start) else {
        return false;
    };
    let span = find_statement_span(
        &lines,
        line_no.saturating_sub(1),
        function_start,
        function_end,
    );
    let statement = lines[span.0..=span.1].join("\n");
    stable_hash(&statement) == replacement.expected_hash
}

fn is_protected_target_or_setup_function(
    container: Option<&str>,
    function: Option<&str>,
    validation_target: Option<&HarnessValidationTarget>,
) -> bool {
    let Some(target) = validation_target else {
        return false;
    };
    if container != Some(target.match_contract.as_str()) {
        return false;
    }
    matches!(function, Some(name) if name == target.match_test || name == "setUp")
}

fn error_line_is_protected_target_or_setup_function(
    lines: &[&str],
    line_no: usize,
    validation_target: Option<&HarnessValidationTarget>,
) -> bool {
    let container = find_enclosing_container_start(lines, line_no)
        .and_then(|idx| parse_container_name(lines[idx].trim_start()));
    let function = find_enclosing_function_start(lines, line_no)
        .and_then(|idx| parse_function_name(lines[idx].trim_start()));
    is_protected_target_or_setup_function(
        container.as_deref(),
        function.as_deref(),
        validation_target,
    )
}

fn error_line_is_exact_target_function(
    lines: &[&str],
    line_no: usize,
    target: &HarnessValidationTarget,
) -> bool {
    let container = find_enclosing_container_start(lines, line_no)
        .and_then(|idx| parse_container_name(lines[idx].trim_start()));
    let function = find_enclosing_function_start(lines, line_no)
        .and_then(|idx| parse_function_name(lines[idx].trim_start()));
    container.as_deref() == Some(target.match_contract.as_str())
        && function.as_deref() == Some(target.match_test.as_str())
}

fn log_unresolved_target_statement_slice(
    target: &HarnessValidationTarget,
    line_no: usize,
    reason: &str,
) {
    crate::execution_log::detail(
        "unresolved_target_statement_slice",
        format!(
            "reason={} target={}::{} line={}",
            reason, target.match_contract, target.match_test, line_no
        ),
    );
}

fn find_statement_span(
    lines: &[&str],
    error_idx: usize,
    lower: usize,
    upper: usize,
) -> (usize, usize) {
    let mut start = error_idx;
    let mut paren = 0i32;
    let mut bracket = 0i32;
    let mut brace = 0i32;
    while start > lower {
        let prev = lines[start - 1].trim();
        if prev.ends_with(';') && paren == 0 && bracket == 0 && brace == 0 {
            break;
        }
        if prev.ends_with('{') && paren == 0 && bracket == 0 {
            break;
        }
        update_reverse_depth(prev, &mut paren, &mut bracket, &mut brace);
        start -= 1;
    }

    let mut end = error_idx;
    paren = 0;
    bracket = 0;
    brace = 0;
    while end < upper {
        let current = lines[end].trim();
        update_forward_depth(current, &mut paren, &mut bracket, &mut brace);
        if current.ends_with(';') && paren <= 0 && bracket <= 0 && brace <= 0 {
            break;
        }
        end += 1;
    }
    (start, end.min(upper))
}

fn match_statement_in_source(fragment: &str, source_function_lines: &[&str]) -> Option<String> {
    let fragment_tokens = identifiers_in_line(fragment);
    let fragment_head = statement_call_or_assignment_head(fragment);
    let mut best: Option<(usize, usize, usize, usize)> = None;
    for idx in 0..source_function_lines.len() {
        let span = find_statement_span(
            source_function_lines,
            idx,
            0,
            source_function_lines.len().saturating_sub(1),
        );
        let statement = source_function_lines[span.0..=span.1].join("\n");
        if let Some(fragment_head) = fragment_head.as_ref() {
            if statement_call_or_assignment_head(&statement).as_deref()
                != Some(fragment_head.as_str())
            {
                continue;
            }
        }
        if !statement_contains_fragment_signal(&statement, fragment, &fragment_tokens) {
            continue;
        }
        let score = statement_similarity_score(&statement, fragment, &fragment_tokens)
            + usize::from(statement.contains(fragment.trim().trim_matches(',')));
        if score == 0 {
            continue;
        }
        let line_count = span.1.saturating_sub(span.0) + 1;
        if best
            .map(|(_, _, best_score, best_line_count)| {
                score > best_score || (score == best_score && line_count < best_line_count)
            })
            .unwrap_or(true)
        {
            best = Some((span.0, span.1, score, line_count));
        }
    }
    best.map(|(start, end, _, _)| source_function_lines[start..=end].join("\n"))
}

fn statement_similarity_score(statement: &str, source: &str, source_tokens: &[String]) -> usize {
    let mut score = source_tokens
        .iter()
        .filter(|token| contains_identifier(statement, token))
        .count();
    let statement_head = statement_call_or_assignment_head(statement);
    let source_head = statement_call_or_assignment_head(source);
    if statement_head.is_some() && statement_head == source_head {
        score += 8;
    }
    score
}

fn statement_call_or_assignment_head(statement: &str) -> Option<String> {
    let normalized = statement
        .lines()
        .map(str::trim)
        .filter(|line| !line.is_empty() && !line.starts_with("//"))
        .collect::<Vec<_>>()
        .join(" ");
    if let Some(before_paren) = normalized.split('(').next() {
        let head = before_paren
            .split_whitespace()
            .last()
            .unwrap_or_default()
            .trim_matches(|ch: char| !ch.is_ascii_alphanumeric() && ch != '_');
        if !head.is_empty() {
            return Some(head.to_string());
        }
    }
    normalized
        .split('=')
        .next()
        .and_then(|head| head.split_whitespace().last())
        .map(str::trim)
        .filter(|head| !head.is_empty())
        .map(str::to_string)
}

fn statement_contains_fragment_signal(statement: &str, fragment: &str, tokens: &[String]) -> bool {
    let normalized_fragment = fragment.trim().trim_matches(',').trim();
    (!normalized_fragment.is_empty() && statement.contains(normalized_fragment))
        || tokens
            .iter()
            .any(|token| contains_identifier(statement, token))
        || (is_dangling_closing_call(fragment.trim()) && statement.contains(");"))
}

fn update_forward_depth(line: &str, paren: &mut i32, bracket: &mut i32, brace: &mut i32) {
    *paren += line.matches('(').count() as i32 - line.matches(')').count() as i32;
    *bracket += line.matches('[').count() as i32 - line.matches(']').count() as i32;
    *brace += line.matches('{').count() as i32 - line.matches('}').count() as i32;
}

fn update_reverse_depth(line: &str, paren: &mut i32, bracket: &mut i32, brace: &mut i32) {
    *paren += line.matches(')').count() as i32 - line.matches('(').count() as i32;
    *bracket += line.matches(']').count() as i32 - line.matches('[').count() as i32;
    *brace += line.matches('}').count() as i32 - line.matches('{').count() as i32;
}

fn try_repair_duplicate_modifier_conflict(code: &str, errors: &[CompilerError]) -> Option<String> {
    let mut conflict_targets = Vec::new();
    for err in errors {
        if !(err.message.contains("must override modifier")
            && err
                .message
                .contains("Two or more base classes define modifier with same name"))
        {
            continue;
        }
        let modifier_name =
            duplicate_modifier_name(&err.message).unwrap_or_else(|| "onlyOwner".to_string());
        if let Some(line_no) = duplicate_modifier_primary_line(err).or(err.line) {
            conflict_targets.push((line_no, modifier_name));
        }
    }
    if conflict_targets.is_empty() {
        return None;
    }

    let mut current = code.to_string();
    let mut inserted = 0usize;
    let mut seen_targets = HashSet::new();
    for (line_no, modifier_name) in conflict_targets {
        let container_name = {
            let lines: Vec<&str> = current.lines().collect();
            find_enclosing_container_start(&lines, line_no)
                .and_then(|idx| parse_container_name(lines[idx].trim_start()))
        };
        if let Some(container_name) = container_name {
            if !seen_targets.insert((container_name, modifier_name.clone())) {
                continue;
            }
        }
        if let Some(repaired) =
            insert_duplicate_modifier_override(&current, line_no, &modifier_name)
        {
            current = repaired;
            inserted += 1;
        }
    }

    if inserted == 0 {
        None
    } else {
        println!(
            "    -> Inserted {} explicit modifier override(s) for duplicate base providers.",
            inserted
        );
        Some(current)
    }
}

fn insert_duplicate_modifier_override(
    code: &str,
    line_no: usize,
    modifier_name: &str,
) -> Option<String> {
    let lines: Vec<&str> = code.lines().collect();
    let container_start = find_enclosing_container_start(&lines, line_no)?;
    let container_end = find_block_end(&lines, container_start)?;
    if lines[container_start]
        .trim_start()
        .starts_with("interface ")
    {
        return None;
    }
    let container_source = lines[container_start..=container_end].join("\n");
    let pattern = format!("modifier {}(", modifier_name);
    if container_source
        .lines()
        .any(|line| line.trim_start().starts_with(&pattern))
    {
        return None;
    }

    let container_header = lines[container_start..=container_end]
        .iter()
        .take(20)
        .map(|line| line.trim())
        .collect::<Vec<_>>()
        .join(" ");
    let base_names = parse_base_definition_names(&container_header);
    let providers = base_names
        .iter()
        .filter(|base| top_level_container_defines_modifier(code, base, modifier_name))
        .cloned()
        .collect::<Vec<_>>();
    if providers.len() < 2 {
        return None;
    }

    let override_block = format!(
        "    modifier {}() override({}) {{\n        _;\n    }}",
        modifier_name,
        providers.join(", ")
    );
    let mut out = Vec::new();
    for line in lines.iter().take(container_end) {
        out.push((*line).to_string());
    }
    out.push(override_block);
    for line in lines.iter().skip(container_end) {
        out.push((*line).to_string());
    }
    Some(out.join("\n"))
}

fn try_restore_interface_bases_from_source(
    code: &str,
    errors: &[CompilerError],
    source_index: &SourceIndex,
) -> Option<DeterministicRepair> {
    let lines: Vec<&str> = code.lines().collect();
    let mut names = Vec::new();

    for err in errors {
        if err
            .message
            .contains("Interfaces can only inherit from other interfaces")
        {
            let Some(line_no) = err.line else {
                continue;
            };
            let Some(line) = lines.get(line_no.saturating_sub(1)) else {
                continue;
            };
            if let Some(column) = err.column {
                if let Some(name) = identifier_at_column(line, column) {
                    names.push(name);
                }
            }
            if line.trim_start().starts_with("interface ") {
                names.extend(parse_base_definition_names(line));
            }
        }

        if err.message.contains("must override modifier")
            && err
                .message
                .contains("Two or more base classes define modifier with same name")
        {
            let Some(line_no) = duplicate_modifier_primary_line(err).or(err.line) else {
                continue;
            };
            let Some(line) = lines.get(line_no.saturating_sub(1)) else {
                continue;
            };
            if line.trim_start().starts_with("interface ") {
                names.extend(parse_base_definition_names(line));
            }
        }
    }

    let mut current = code.to_string();
    let mut replacements = Vec::new();
    let mut seen = HashSet::new();
    for name in names {
        if !seen.insert(name.clone()) {
            continue;
        }
        let Some(source_container) = source_index.container(&name) else {
            continue;
        };
        if source_container.kind != "interface" {
            continue;
        }
        if top_level_definition_kind_in_code(&current, &name).as_deref() == Some("interface") {
            continue;
        }
        let Some(repaired) =
            replace_top_level_definition_by_name(&current, &name, &source_container.source)
        else {
            continue;
        };
        current = repaired;
        replacements.push(ContainerReplacement {
            container_name: name,
            expected_hash: source_container.body_hash,
        });
    }

    if replacements.is_empty() {
        None
    } else {
        println!(
            "    -> Restored {} interface base definition(s) from source.",
            replacements.len()
        );
        Some(DeterministicRepair::source_backed_containers(
            current,
            Vec::new(),
            replacements,
        ))
    }
}

fn try_restore_declaration_function_from_source(
    code: &str,
    errors: &[CompilerError],
    source_index: &SourceIndex,
) -> Option<DeterministicRepair> {
    let lines: Vec<&str> = code.lines().collect();
    for err in errors {
        if err.category != CompilerErrorCategory::Declaration
            || !err
                .message
                .contains("Different number of arguments in return statement")
        {
            continue;
        }
        let line_no = err.line?;
        let (function_start, function_end, target, source) =
            source_function_replacement_for_line(&lines, line_no, source_index)?;
        let mut repaired = Vec::new();
        for line in lines.iter().take(function_start) {
            repaired.push((*line).to_string());
        }
        repaired.push(source);
        for line in lines.iter().skip(function_end + 1) {
            repaired.push((*line).to_string());
        }
        println!("    -> Restored source function for declaration/return arity mismatch.");
        return Some(DeterministicRepair::source_backed(
            repaired.join("\n"),
            vec![target],
        ));
    }

    None
}

fn restore_known_fragment_support(
    code: &str,
    line_no: usize,
    column: Option<usize>,
) -> Option<String> {
    let lines: Vec<&str> = code.lines().collect();
    let line = lines
        .get(line_no.saturating_sub(1))
        .copied()
        .unwrap_or_default();
    let mut synthetic_error = CompilerError {
        code: None,
        message: String::new(),
        file: None,
        line: Some(line_no),
        column,
        category: CompilerErrorCategory::MissingSymbol,
        snippet: Vec::new(),
    };

    for symbol in missing_symbol_candidates(line, column) {
        match symbol.as_str() {
            "a0" | "a1" | "b0" | "b1" => {
                synthetic_error.message = format!("Identifier \"{}\" not found.", symbol);
                return try_repair_balance_delta_add(code, &[synthetic_error]);
            }
            _ => {}
        }
    }

    if line.contains(".toInt128()") {
        synthetic_error.message = "Member \"toInt128\" not found".to_string();
        return try_repair_balance_delta_add(code, &[synthetic_error]);
    }

    None
}

fn try_repair_balance_delta_add(code: &str, errors: &[CompilerError]) -> Option<String> {
    let has_balance_delta_add_error = errors.iter().any(|err| {
        err.message.contains("Identifier \"a0\" not found")
            || err.message.contains("Identifier \"b0\" not found")
            || err.message.contains("Identifier \"a1\" not found")
            || err.message.contains("Identifier \"b1\" not found")
            || err.message.contains("Member \"toInt128\" not found")
            || err
                .message
                .contains("Type int256 is not implicitly convertible to expected type int128")
    });
    if !has_balance_delta_add_error {
        return None;
    }

    let lines: Vec<&str> = code.lines().collect();
    let mut replacements = Vec::new();
    for (idx, line) in lines.iter().enumerate() {
        let trimmed = line.trim_start();
        let is_add = trimmed.starts_with("function add(BalanceDelta a, BalanceDelta b)");
        let is_sub = trimmed.starts_with("function sub(BalanceDelta a, BalanceDelta b)");
        if !is_add && !is_sub {
            continue;
        }
        let function_end = find_function_end(&lines, idx)?;
        let current_function = lines[idx..=function_end].join("\n");
        if !current_function.contains("res0 := add(a0, b0)")
            && !current_function.contains("res1 := add(a1, b1)")
            && !current_function.contains("res0 := sub(a0, b0)")
            && !current_function.contains("res1 := sub(a1, b1)")
            && !current_function.contains("res0.toInt128()")
            && !current_function.contains("BalanceDelta.unwrap(a)")
        {
            continue;
        }

        let operator = if is_add { "+" } else { "-" };
        let name = if is_add { "add" } else { "sub" };
        let replacement = format!(
            "function {name}(BalanceDelta a, BalanceDelta b) pure returns (BalanceDelta) {{\n    int128 a0 = int128(BalanceDelta.unwrap(a));\n    int128 a1 = int128(BalanceDelta.unwrap(a) >> 128);\n    int128 b0 = int128(BalanceDelta.unwrap(b));\n    int128 b1 = int128(BalanceDelta.unwrap(b) >> 128);\n    return toBalanceDelta(int128(a0 {operator} b0), int128(a1 {operator} b1));\n}}"
        );
        replacements.push((idx, function_end, replacement));
    }

    if replacements.is_empty() {
        return None;
    }

    let mut out = Vec::new();
    let mut next_replacement = 0usize;
    let mut idx = 0usize;
    while idx < lines.len() {
        if next_replacement < replacements.len() && idx == replacements[next_replacement].0 {
            let (_, end, replacement) = &replacements[next_replacement];
            out.push(replacement.clone());
            idx = end + 1;
            next_replacement += 1;
        } else {
            out.push(lines[idx].to_string());
            idx += 1;
        }
    }

    println!(
        "    -> Rebuilt {} corrupted BalanceDelta arithmetic helper(s).",
        replacements.len()
    );
    Some(out.join("\n"))
}

fn duplicate_modifier_primary_line(err: &CompilerError) -> Option<usize> {
    err.snippet.iter().find_map(|snippet_line| {
        let (line_no, rest) = snippet_line.split_once('|')?;
        let source_line = rest.trim_start();
        if source_line.starts_with("contract ")
            || source_line.starts_with("abstract contract ")
            || source_line.starts_with("interface ")
            || source_line.starts_with("library ")
        {
            line_no.trim().parse::<usize>().ok()
        } else {
            None
        }
    })
}

fn duplicate_modifier_name(message: &str) -> Option<String> {
    let (_, rest) = message.split_once("modifier \"")?;
    let (name, _) = rest.split_once('"')?;
    Some(name.to_string())
}

fn top_level_container_defines_modifier(
    code: &str,
    container_name: &str,
    modifier_name: &str,
) -> bool {
    let Some(container) = extract_container_from_source(code, container_name) else {
        return false;
    };
    let pattern = format!("modifier {}(", modifier_name);
    container
        .lines()
        .any(|line| line.trim_start().starts_with(&pattern))
}

fn try_remove_unexpected_trailing_commas(code: &str, errors: &[CompilerError]) -> Option<String> {
    let lines: Vec<&str> = code.lines().collect();
    let mut changed = false;
    let mut repaired_lines = lines
        .iter()
        .map(|line| (*line).to_string())
        .collect::<Vec<_>>();

    for err in errors {
        let Some(line_no) = err.line else {
            continue;
        };
        let idx = line_no.saturating_sub(1);
        let Some(line) = lines.get(idx) else {
            continue;
        };
        let trimmed = line.trim();

        let explicit_comma_error = err.message.contains("Unexpected trailing comma");
        let local_comma_before_close = trimmed.contains(",)") || trimmed.contains(",]");
        if !explicit_comma_error && !local_comma_before_close {
            continue;
        }

        let next = line.replace(",)", ")").replace(",]", "]");
        if next != *line {
            repaired_lines[idx] = next;
            changed = true;
        }
    }

    if !changed {
        return None;
    }

    println!("    -> Removed unexpected trailing comma near compiler error.");
    Some(repaired_lines.join("\n"))
}

fn try_remove_trailing_comma_before_call_close(
    code: &str,
    errors: &[CompilerError],
) -> Option<String> {
    let lines: Vec<&str> = code.lines().collect();
    let mut repaired_lines = lines
        .iter()
        .map(|line| (*line).to_string())
        .collect::<Vec<_>>();
    let mut changed = false;

    let should_sweep = errors.iter().any(|err| {
        err.category == CompilerErrorCategory::Syntax
            && (looks_like_parser_error(err)
                || err.message.contains("Expected primary expression")
                || err.message.contains("Expected ','")
                || err.message.contains("Expected ';'"))
    });

    if should_sweep {
        // Collect function bounds for errors to restrict the sweep
        let mut sweep_bounds = Vec::new();
        for err in errors {
            if err.category != CompilerErrorCategory::Syntax {
                continue;
            }
            if let Some(line_no) = err.line {
                if let Some(start) = find_enclosing_function_start(&lines, line_no) {
                    if let Some(end) = find_function_end(&lines, start) {
                        sweep_bounds.push((start, end));
                    }
                }
            }
        }

        for (idx, line) in lines.iter().enumerate() {
            if !is_dangling_closing_call(line.trim()) {
                continue;
            }

            // Only sweep if the dangling call is inside the error's function scope
            if !sweep_bounds.iter().any(|(s, e)| idx >= *s && idx <= *e) {
                continue;
            }

            let Some(prev_idx) = previous_nonempty_line_index(&lines, idx) else {
                continue;
            };
            let Some(previous) = repaired_lines.get_mut(prev_idx) else {
                continue;
            };
            let trimmed = previous.trim_end();
            if !trimmed.ends_with(',') {
                continue;
            }
            let without_comma = trimmed.trim_end_matches(',');
            if without_comma.trim().is_empty() {
                continue;
            }
            let trailing_ws = &previous[trimmed.len()..];
            *previous = format!("{}{}", without_comma, trailing_ws);
            changed = true;
        }
    }

    for err in errors {
        if err.category != CompilerErrorCategory::Syntax || !looks_like_parser_error(err) {
            continue;
        }
        let Some(line_no) = err.line else {
            continue;
        };
        let idx = line_no.saturating_sub(1);
        let Some(line) = lines.get(idx) else {
            continue;
        };
        if !is_dangling_closing_call(line.trim()) {
            continue;
        }

        let Some(prev_idx) = previous_nonempty_line_index(&lines, idx) else {
            continue;
        };
        let Some(previous) = repaired_lines.get_mut(prev_idx) else {
            continue;
        };
        let trimmed = previous.trim_end();
        if !trimmed.ends_with(',') {
            continue;
        }
        let without_comma = trimmed.trim_end_matches(',');
        if without_comma.trim().is_empty() {
            continue;
        }
        let trailing_ws = &previous[trimmed.len()..];
        *previous = format!("{}{}", without_comma, trailing_ws);
        changed = true;
    }

    if !changed {
        return None;
    }

    println!("    -> Removed trailing comma before multiline call close.");
    Some(repaired_lines.join("\n"))
}

fn try_remove_trailing_enum_commas(code: &str, errors: &[CompilerError]) -> Option<String> {
    let lines: Vec<&str> = code.lines().collect();
    let mut repaired_lines = lines
        .iter()
        .map(|line| (*line).to_string())
        .collect::<Vec<_>>();
    let mut changed = false;

    for err in errors {
        if err.category != CompilerErrorCategory::Syntax
            || !err.message.contains("Expected identifier after ','")
        {
            continue;
        }
        let Some(line_no) = err.line else {
            continue;
        };
        let idx = line_no.saturating_sub(1);
        let Some(line) = lines.get(idx) else {
            continue;
        };
        if line.trim() != "}" {
            continue;
        }
        let Some(prev_idx) = previous_nonempty_line_index(&lines, idx) else {
            continue;
        };
        if !lines[prev_idx].trim_end().ends_with(',') || !is_inside_enum_block(&lines, idx) {
            continue;
        }

        let previous = &mut repaired_lines[prev_idx];
        let trimmed = previous.trim_end();
        let without_comma = trimmed.trim_end_matches(',');
        let trailing_ws = &previous[trimmed.len()..];
        *previous = format!("{}{}", without_comma, trailing_ws);
        changed = true;
    }

    if !changed {
        return None;
    }

    println!("    -> Removed trailing comma before enum close.");
    Some(repaired_lines.join("\n"))
}

fn is_inside_enum_block(lines: &[&str], close_idx: usize) -> bool {
    let mut balance = 0i32;
    for idx in (0..close_idx).rev() {
        let line = lines[idx];
        balance += line.matches('}').count() as i32;
        balance -= line.matches('{').count() as i32;
        let trimmed = line.trim_start();
        if balance < 0 {
            return trimmed.starts_with("enum ");
        }
    }
    false
}

fn try_remove_duplicate_top_level_definitions(
    code: &str,
    errors: &[CompilerError],
) -> Option<String> {
    if !errors.iter().any(|err| {
        err.category == CompilerErrorCategory::Duplicate
            && err.message.contains("Identifier already declared")
    }) {
        return None;
    }

    let chunks = split_top_level_chunks_with_spans(code);
    let mut remove_indices = HashSet::new();

    for err in errors {
        if err.category != CompilerErrorCategory::Duplicate
            || !err.message.contains("Identifier already declared")
        {
            continue;
        }
        let Some(line_no) = err.line else {
            continue;
        };
        let Some(current_idx) = chunks
            .iter()
            .position(|chunk| line_no >= chunk.start_line && line_no <= chunk.end_line)
        else {
            continue;
        };
        let names = normalizer::top_level_definition_names(&chunks[current_idx].text);
        for name in names {
            let duplicate_indices = chunks
                .iter()
                .enumerate()
                .filter(|(_, chunk)| {
                    normalizer::top_level_definition_names(&chunk.text).contains(&name)
                })
                .map(|(idx, _)| idx)
                .collect::<Vec<_>>();
            if duplicate_indices.len() < 2 {
                continue;
            }

            if name == "Vm" {
                if let Some(contract_idx) = duplicate_indices.iter().copied().find(|idx| {
                    chunks[*idx].text.trim_start().starts_with("contract Vm")
                        && duplicate_indices.iter().any(|other_idx| {
                            chunks[*other_idx]
                                .text
                                .trim_start()
                                .starts_with("interface Vm")
                        })
                }) {
                    remove_indices.insert(contract_idx);
                    continue;
                }
            }

            if is_stub_like_container(&chunks[current_idx].text) {
                remove_indices.insert(current_idx);
            }
        }
    }

    if remove_indices.is_empty() {
        return None;
    }

    let repaired = chunks
        .into_iter()
        .enumerate()
        .filter_map(|(idx, chunk)| (!remove_indices.contains(&idx)).then_some(chunk.text))
        .collect::<Vec<_>>()
        .join("\n\n");

    println!("    -> Removed duplicate top-level stub definition(s).");
    Some(repaired)
}

/// Fix Yul-style comma-separated assignments that leak outside assembly blocks.
/// Error: "Expected ';' but got ','" on lines like `L = lowerTick, U = upperTick`
/// Strategy:
///   1. If inside `assembly { }` — keep, commas are valid Yul
///   2. If outside assembly — wrap orphaned Yul lines in `assembly { ... }`
///   3. Also clean up orphan `tick`/identifer residue lines that follow Yul patterns
fn try_fix_yul_comma_error(code: &str, errors: &[CompilerError]) -> Option<String> {
    let lines: Vec<&str> = code.lines().collect();
    let mut changed = false;
    let mut repaired_lines: Vec<String> = lines.iter().map(|line| (*line).to_string()).collect();
    let mut processed = std::collections::HashSet::new();

    for err in errors {
        if !err.message.contains("Expected ';' but got ','") {
            continue;
        }
        let Some(line_no) = err.line else {
            continue;
        };
        let idx = line_no.saturating_sub(1);
        if processed.contains(&idx) {
            continue;
        }
        let Some(line) = lines.get(idx) else {
            continue;
        };
        let trimmed = line.trim();

        // Check if inside an assembly block — if so, commas are valid Yul
        if is_inside_assembly_block(&lines, idx) {
            continue;
        }

        // Verify this line has Yul assignment patterns.
        // Yul always uses `:=` for assignment; `=` is Solidity and NOT Yul.
        let has_yul_assign = trimmed.contains(":=");
        let has_yul_tokens = [
            "let ",
            "mstore",
            "mload",
            "sload",
            "sstore",
            "add(",
            "sub(",
            "mul(",
            "div(",
            "mod(",
            "shr(",
            "shl(",
            "signextend",
            "keccak256",
            "and(",
            "or(",
            "xor(",
            "not(",
        ]
        .iter()
        .any(|kw| trimmed.contains(kw));
        // If the line uses Solidity `=` (not Yul `:=`) with no Yul tokens, skip
        if trimmed.contains(" = ") && !has_yul_assign {
            continue;
        }
        if !has_yul_assign && !has_yul_tokens {
            continue;
        }

        // Compute the indentation
        let indent = line[..line.len() - trimmed.len()].to_string();

        // Collect the Yul-looking lines: this error line + adjacent Yul residue
        let mut yul_start = idx;
        let mut yul_end = idx;

        // Look backward for adjacent Yul lines (max 3 lines up)
        for _ in 1..=3 {
            if yul_start == 0 {
                break;
            }
            let prev = lines[yul_start - 1].trim();
            if prev.is_empty() || prev.starts_with("//") {
                break;
            }
            if has_yul_assign
                || ["let ", "mstore", "mload", "sload"]
                    .iter()
                    .any(|kw| prev.contains(kw))
            {
                yul_start -= 1;
            } else {
                break;
            }
        }

        // Look forward for adjacent Yul residue lines (like orphan `tick`)
        for _ in 1..=2 {
            let next_idx = yul_end + 1;
            if next_idx >= lines.len() {
                break;
            }
            let next = lines[next_idx].trim();
            if next.is_empty() || next.starts_with("//") {
                break;
            }
            // Detect orphan residue: short lowercase identifiers that look like Yul remnants
            let is_residue = next.len() < 20
                && next.chars().all(|c| c.is_ascii_alphanumeric() || c == '_')
                && !next.contains('=')
                && !next.contains('(')
                && !next.contains(';');
            if is_residue || has_yul_assign {
                yul_end = next_idx;
                changed = true; // mark residue line for deletion/wrapping
            } else {
                break;
            }
        }

        // Build the assembly block wrapping these lines
        let mut assembly_body = String::new();
        for i in yul_start..=yul_end {
            let body_line = lines[i].trim();
            if body_line.is_empty() || body_line.starts_with("//") {
                continue;
            }
            // If the line already ends with something valid, keep as is;
            // otherwise ensure Yul statements are properly formatted
            let clean = body_line.trim_end_matches(',');
            assembly_body.push_str(&format!("        {}\n", clean));
            processed.insert(i);
            changed = true;
        }

        if assembly_body.trim().is_empty() {
            continue;
        }

        // Replace the first Yul line with assembly block start
        // and mark the rest for deletion
        repaired_lines[yul_start] = format!("{}assembly {{\n{}{}}}", indent, assembly_body, indent);

        // Mark remaining Yul lines for deletion
        for i in (yul_start + 1)..=yul_end {
            if i < repaired_lines.len() {
                repaired_lines[i] = String::new();
            }
        }

        println!(
            "    -> Wrapped orphaned Yul lines {}-{} in assembly block.",
            yul_start + 1,
            yul_end + 1
        );
    }

    if !changed {
        return None;
    }

    // Remove empty lines we marked
    let result: Vec<String> = repaired_lines
        .into_iter()
        .enumerate()
        .filter(|(i, line)| !line.is_empty() || processed.contains(i))
        .map(|(_, line)| line)
        .collect();

    Some(result.join("\n"))
}

/// Check if a given line index is inside an `assembly { ... }` block
fn is_inside_assembly_block(lines: &[&str], idx: usize) -> bool {
    let lower = idx.saturating_sub(100);
    let mut depth: i32 = 0;
    for i in (lower..=idx).rev() {
        let trimmed = lines[i].trim();
        // Track brace depth
        let opens = trimmed.matches('{').count() as i32;
        let closes = trimmed.matches('}').count() as i32;
        depth += closes - opens;

        if depth < 0 {
            depth = 0;
            // Check if this opening brace belongs to an assembly block
            if trimmed.contains("assembly ")
                || trimmed.contains("assembly(")
                || trimmed == "assembly"
            {
                return true;
            }
        }
    }
    false
}

fn try_comment_orphaned_call_closes(code: &str, errors: &[CompilerError]) -> Option<String> {
    let lines: Vec<&str> = code.lines().collect();
    let mut changed = false;
    let mut repaired = Vec::with_capacity(lines.len());
    let error_lines = errors
        .iter()
        .filter(|err| err.category == CompilerErrorCategory::Syntax && looks_like_parser_error(err))
        .filter_map(|err| err.line)
        .collect::<HashSet<_>>();

    if error_lines.is_empty() {
        return None;
    }

    for (idx, line) in lines.iter().enumerate() {
        let line_no = idx + 1;
        let trimmed = line.trim();
        if error_lines.contains(&line_no)
            && is_dangling_closing_call(trimmed)
            && !previous_line_opens_call(&lines, idx)
            && !previous_nonempty_line(&lines, idx)
                .map(|previous| previous.trim_end().ends_with(','))
                .unwrap_or(false)
        {
            repaired.push(format!("// [AUTO_COMPILE_FIX_ORPHAN_CLOSE] {}", line));
            changed = true;
        } else {
            repaired.push((*line).to_string());
        }
    }

    if !changed {
        return None;
    }

    println!("    -> Commented orphaned call close(s) to preserve compilability.");
    Some(repaired.join("\n"))
}

fn try_deterministic_syntax_repair_with_context(
    code: &str,
    errors: &[CompilerError],
    original_source: &str,
    source_index: &SourceIndex,
    protected_statements: &[StatementReplacement],
    protected_functions: &[SourceReplacement],
    protected_containers: &[ContainerReplacement],
    restore_history: &RestoreHistory,
    baseline_output_lines: usize,
    validation_target: Option<&HarnessValidationTarget>,
) -> Option<DeterministicRepair> {
    let lines: Vec<&str> = code.lines().collect();

    if let Some(repair) = try_target_statement_restore(
        code,
        errors,
        source_index,
        protected_statements,
        restore_history,
        baseline_output_lines,
        validation_target,
    ) {
        return Some(repair);
    }

    if let Some(repair) = try_syntax_error_guided_source_restore(
        code,
        errors,
        source_index,
        protected_functions,
        protected_containers,
        restore_history,
        baseline_output_lines,
        validation_target,
    ) {
        return Some(repair);
    }

    if let Some(repair) = try_restore_using_libraries_from_errors(code, errors, source_index) {
        return Some(repair);
    }

    // Fast local fixes first: these are intentionally small compile-oriented
    // patches. Keep them local to compiler-reported lines so deterministic
    // repair converges and does not repeatedly mutate unrelated code.
    if let Some(repaired) = try_remove_unexpected_trailing_commas(code, errors) {
        return Some(DeterministicRepair::plain(repaired));
    }

    if let Some(repaired) = try_remove_trailing_enum_commas(code, errors) {
        return Some(DeterministicRepair::plain(repaired));
    }

    if let Some(repaired) = try_remove_duplicate_top_level_definitions(code, errors) {
        return Some(DeterministicRepair::source_backed_code(repaired));
    }

    if let Some(repair) = try_restore_interface_bases_from_source(code, errors, source_index) {
        return Some(repair);
    }

    if let Some(repair) = try_restore_declaration_function_from_source(code, errors, source_index) {
        return Some(repair);
    }

    // P1: Fix Yul-style comma separators inside assembly blocks
    // Error: "Expected ';' but got ','" on a line like "L = lowerTick, U = upperTick"
    if let Some(repaired) = try_fix_yul_comma_error(code, errors) {
        return Some(DeterministicRepair::plain(repaired));
    }

    if let Some(repaired) = try_repair_balance_delta_add(code, errors) {
        return Some(DeterministicRepair::plain(repaired));
    }

    if let Some(repaired) = try_repair_duplicate_modifier_conflict(code, errors) {
        return Some(DeterministicRepair::plain(repaired));
    }

    // Local `arg, );` cleanup should run before source-backed function repair:
    // normalizer/cleanup may drop optional assertion message strings while
    // leaving the preceding comma, and replacing protected business logic is a
    // heavier repair than removing that comma.
    if let Some(repaired) = try_remove_trailing_comma_before_call_close(code, errors) {
        return Some(DeterministicRepair::plain(repaired));
    }

    if let Some(repair) = try_batch_source_function_repair(
        code,
        errors,
        source_index,
        restore_history,
        baseline_output_lines,
        validation_target,
    ) {
        return Some(repair);
    }

    if let Some(repair) = try_statement_span_source_repair(code, errors, source_index) {
        return Some(repair);
    }

    if let Some(repair) = try_batch_source_container_repair(
        code,
        errors,
        source_index,
        restore_history,
        baseline_output_lines,
    ) {
        return Some(repair);
    }

    if let Some(repaired) = try_comment_orphaned_call_closes(code, errors) {
        return Some(DeterministicRepair::plain(repaired));
    }

    // Pre-pass: a naked call close with no visible opener usually means the
    // surrounding function body lost one or more multiline call/assignment
    // lines. Prefer source-aligned function recovery before broad comma cleanup.
    for err in errors {
        let Some(line_no) = err.line else {
            continue;
        };
        let Some(line) = lines.get(line_no.saturating_sub(1)) else {
            continue;
        };
        if err.category == CompilerErrorCategory::Syntax
            && is_dangling_closing_call(line.trim())
            && !previous_line_opens_call(&lines, line_no.saturating_sub(1))
            && !previous_nonempty_line(&lines, line_no.saturating_sub(1))
                .map(|previous| previous.trim_end().ends_with(','))
                .unwrap_or(false)
        {
            if error_line_is_protected_target_or_setup_function(&lines, line_no, validation_target)
            {
                continue;
            }
            if let Some((start, end, target, source)) =
                source_function_replacement_for_line(&lines, line_no, source_index)
            {
                let current_function = lines[start..=end].join("\n");
                if source_function_is_better(&source, &current_function) {
                    let mut repaired = Vec::new();
                    for line in lines.iter().take(start) {
                        repaired.push((*line).to_string());
                    }
                    repaired.push(source);
                    for line in lines.iter().skip(end + 1) {
                        repaired.push((*line).to_string());
                    }
                    println!("    -> Replaced function containing orphaned call close.");
                    return Some(DeterministicRepair::source_backed(
                        repaired.join("\n"),
                        vec![target],
                    ));
                }
            }

            if let Some(repaired) =
                replace_enclosing_function_from_source(code, line_no, original_source)
            {
                println!("    -> Replaced function containing orphaned call close.");
                return Some(DeterministicRepair::plain(repaired));
            }
        }
    }

    // Pass 2: Other syntax repairs
    let mut remove = std::collections::HashSet::new();
    for err in errors {
        let Some(line_no) = err.line else {
            continue;
        };
        let Some(line) = lines.get(line_no.saturating_sub(1)) else {
            continue;
        };
        let in_protected_target =
            error_line_is_protected_target_or_setup_function(&lines, line_no, validation_target);

        if err.category == CompilerErrorCategory::Syntax && is_dangling_closing_call(line.trim()) {
            if !in_protected_target {
                if let Some(repaired) =
                    replace_enclosing_container_span_from_source(code, line_no, original_source)
                {
                    println!(
                        "    -> Replaced container containing dangling call close at line {}.",
                        line_no
                    );
                    return Some(DeterministicRepair::plain(repaired));
                }

                if let Some(repaired) = replace_enclosing_container_everywhere_from_source(
                    code,
                    line_no,
                    original_source,
                ) {
                    println!(
                        "    -> Replaced all matching containers containing dangling call close at line {}.",
                        line_no
                    );
                    return Some(DeterministicRepair::plain(repaired));
                }

                if let Some(repaired) =
                    replace_enclosing_function_from_source(code, line_no, original_source)
                {
                    println!(
                        "    -> Replaced function containing dangling call close at line {}.",
                        line_no
                    );
                    return Some(DeterministicRepair::plain(repaired));
                }
            }
        }

        if looks_like_parser_error(err) && !in_protected_target {
            if let Some(repaired) =
                replace_enclosing_function_from_source(code, line_no, original_source)
            {
                println!("    -> Replaced corrupted function from original source.");
                return Some(DeterministicRepair::plain(repaired));
            }
            println!(
                "    -> No source function replacement available for parser error at line {}.",
                line_no
            );
        }

        if is_base_precedence_error(err) {
            if let Some(repaired) = repair_base_precedence(code, line_no, original_source) {
                println!("    -> Reordered base definitions before derived definition.");
                return Some(DeterministicRepair::source_backed_code(repaired));
            }
        }

        if is_identifier_not_library_name_error(err) {
            if let Some(repair) = restore_using_library_from_source(code, line_no, source_index) {
                println!("    -> Restored source library referenced by using directive.");
                return Some(repair);
            }
        }

        if is_missing_symbol_error(err) {
            if let Some(repaired) = restore_known_fragment_support(code, line_no, err.column) {
                println!(
                    "    -> Restored deterministic support for a known sliced fragment helper."
                );
                return Some(DeterministicRepair::plain(repaired));
            }

            // P0: Check if the missing symbol is a Yul/EVM opcode used outside assembly
            let candidates = missing_symbol_candidates(line, err.column);
            let all_evm_opcodes = candidates.iter().all(|s| is_evm_opcode(s));
            if all_evm_opcodes && !candidates.is_empty() {
                // The error line uses EVM opcodes outside an assembly block.
                // Try to wrap the enclosing function's problematic statements in assembly.
                if let Some(repaired) = try_wrap_in_assembly(code, line_no) {
                    println!(
                        "    -> Wrapped Yul opcodes ({}) in assembly block at line {}.",
                        candidates.join(", "),
                        line_no
                    );
                    return Some(DeterministicRepair::plain(repaired));
                }
                println!(
                    "    -> Detected EVM opcodes ({}) outside assembly at line {}, but could not auto-wrap. \
                     Skipping symbol lookup for these built-in opcodes.",
                    candidates.join(", "),
                    line_no
                );
                continue;
            }

            if let Some(repair) =
                restore_missing_symbol_dependency_closure(code, line_no, err.column, source_index)
            {
                return Some(repair);
            }

            if let Some(repair) =
                restore_missing_top_level_provider(code, line_no, err.column, source_index)
            {
                println!("    -> Restored missing top-level provider.");
                return Some(repair);
            }

            if let Some(modifier_name) = modifier_candidate_from_signature_line(line) {
                if let Some((container_name, original_container)) =
                    extract_container_defining_symbol(original_source, &modifier_name)
                {
                    let is_heavy = symbol_kind_in_source(original_source, &container_name)
                        .map(|kind| {
                            matches!(
                                kind,
                                "contract" | "abstract contract" | "interface" | "library"
                            )
                        })
                        .unwrap_or(false);
                    if !is_heavy {
                        if let Some(repaired) =
                            replace_container_by_name(code, &container_name, &original_container)
                        {
                            println!(
                                "    -> Replaced modifier provider {} from original source.",
                                container_name
                            );
                            return Some(DeterministicRepair::plain(repaired));
                        }
                    }
                }
            }

            if let Some(repair) = restore_current_container_defining_missing_symbol(
                code,
                line_no,
                err.column,
                original_source,
            ) {
                println!("    -> Restored current container that defines missing member symbol.");
                return Some(repair);
            }

            if let Some(repair) = restore_base_container_defining_missing_symbol(
                code,
                line_no,
                err.column,
                original_source,
            ) {
                println!("    -> Restored base container that defines missing helper symbol.");
                return Some(repair);
            }

            if let Some(repaired) = restore_synthetic_test_support(code, line_no, err.column) {
                println!("    -> Restored synthetic test support for missing harness symbol.");
                return Some(DeterministicRepair::plain(repaired));
            }

            if let Some(repair) = restore_container_for_missing_member(code, err, original_source) {
                println!("    -> Restored provider container for missing member.");
                return Some(repair);
            }

            if let Some(repair) =
                restore_extension_provider_for_missing_member(code, err, source_index)
            {
                println!("    -> Restored extension provider for missing member.");
                return Some(repair);
            }

            if let Some(repaired) = replace_definition_containing_missing_symbol(
                code,
                line_no,
                err.column,
                original_source,
            ) {
                println!(
                    "    -> Replaced definition that declares missing symbol from original source."
                );
                return Some(DeterministicRepair::source_backed_code(repaired));
            }

            if let Some(repaired) =
                replace_enclosing_container_from_source(code, line_no, original_source)
            {
                println!("    -> Replaced incomplete top-level definition from original source.");
                return Some(DeterministicRepair::plain(repaired));
            }

            if let Some(repaired) =
                replace_enclosing_function_from_source(code, line_no, original_source)
            {
                println!("    -> Replaced enclosing function to restore missing local variables.");
                return Some(DeterministicRepair::plain(repaired));
            }

            println!(
                "    -> No source top-level replacement available for missing symbol at line {}.",
                line_no
            );
        }

        if err.category != CompilerErrorCategory::Syntax {
            continue;
        }

        if normalizer::is_removable_residue_line(line.trim()) {
            remove.insert(line_no);
            continue;
        }

        if !in_protected_target {
            if let Some(repaired) =
                replace_enclosing_function_from_source(code, line_no, original_source)
            {
                return Some(DeterministicRepair::plain(repaired));
            }
        }

        if let Some(previous_residue_line) = find_previous_residue_line(&lines, line_no) {
            remove.insert(previous_residue_line);
        }
    }

    if remove.is_empty() {
        return None;
    }

    let repaired = lines
        .iter()
        .enumerate()
        .filter_map(|(idx, line)| {
            let line_no = idx + 1;
            if remove.contains(&line_no) {
                None
            } else {
                Some(*line)
            }
        })
        .collect::<Vec<_>>()
        .join("\n");

    Some(DeterministicRepair::plain(repaired))
}

fn restore_missing_symbol_dependency_closure(
    code: &str,
    line_no: usize,
    column: Option<usize>,
    source_index: &SourceIndex,
) -> Option<DeterministicRepair> {
    let lines: Vec<&str> = code.lines().collect();
    let error_line = lines.get(line_no.saturating_sub(1))?;
    let current_container_start = find_enclosing_container_start(&lines, line_no)?;
    let current_container_end = find_block_end(&lines, current_container_start)?;
    let current_container = lines[current_container_start..=current_container_end].join("\n");
    let current_container_name = parse_container_name(lines[current_container_start].trim_start())?;
    let base_names = parse_base_definition_names(&current_container);
    let mut replacements = Vec::new();

    if normalizer::parse_top_level_definition(error_line.trim_start()).is_some() {
        for base_name in &base_names {
            if base_name == &current_container_name || is_evm_opcode(base_name) {
                continue;
            }
            let Some(source_container) = source_index.container(base_name) else {
                continue;
            };
            let existing_container = extract_container_from_source(code, base_name);
            let existing_is_stub = existing_container
                .as_deref()
                .map(is_stub_like_container)
                .unwrap_or(false);
            if existing_container.is_some() && !existing_is_stub {
                continue;
            }
            replacements.push(ContainerReplacement {
                container_name: base_name.clone(),
                expected_hash: source_container.body_hash,
            });
        }
    }

    for symbol in missing_symbol_candidates(error_line, column) {
        if !replacements.is_empty() {
            break;
        }
        if symbol == current_container_name || is_evm_opcode(&symbol) {
            continue;
        }
        if let Some(source_container) = source_index.container(&symbol) {
            replacements.push(ContainerReplacement {
                container_name: symbol,
                expected_hash: source_container.body_hash,
            });
            break;
        }
        let providers = source_index.providers_for_symbol(&symbol);
        for provider in providers {
            let allowed_base = base_names.iter().any(|base| base == &provider);
            let current_provider = provider == current_container_name;
            if !allowed_base && !current_provider {
                continue;
            }
            let source_container = source_index.container(&provider)?;
            let existing_container = extract_container_from_source(code, &provider);

            if existing_container.is_some() {
                if let Some(member_code) =
                    extract_member_from_container(&source_container.source, &symbol)
                {
                    if let Some(repaired) = inject_into_container(code, &provider, &member_code) {
                        let replacement = MissingSymbolRestoreAction::RestoreFunction {
                            container: provider.clone(),
                            name: symbol.clone(),
                        };
                        return Some(DeterministicRepair::missing_symbol_backed(
                            repaired,
                            vec![replacement],
                        ));
                    }
                }
            }

            let existing_is_stub = existing_container
                .as_deref()
                .map(is_stub_like_container)
                .unwrap_or(false);
            let source_is_small = source_container.source.lines().count() <= 220;
            let is_harness = current_container.contains(" is Test")
                || current_container_name.ends_with("Test")
                || current_container_name == "PoC";
            if !current_provider && !existing_is_stub && !source_is_small {
                continue;
            }
            if current_provider && !source_is_small && !is_harness {
                continue;
            }
            replacements.push(ContainerReplacement {
                container_name: provider,
                expected_hash: source_container.body_hash,
            });
            break;
        }
        if !replacements.is_empty() {
            break;
        }
    }

    if replacements.is_empty() {
        return None;
    }

    append_referenced_container_dependency_closures(
        &mut replacements,
        code,
        &current_container,
        source_index,
    );

    let mut repaired = code.to_string();
    for replacement in &replacements {
        repaired = replace_container_by_source_target(&repaired, replacement, source_index)?;
    }
    println!(
        "    -> Restored missing symbol dependency closure: {}.",
        replacements
            .iter()
            .map(|replacement| replacement.container_name.as_str())
            .collect::<Vec<_>>()
            .join(", ")
    );
    crate::execution_log::detail(
        "resurrection_missing_symbol_closure",
        format!(
            "line={} providers={}",
            line_no,
            replacements
                .iter()
                .map(|replacement| format!(
                    "{}#{}",
                    replacement.container_name, replacement.expected_hash
                ))
                .collect::<Vec<_>>()
                .join(",")
        ),
    );
    Some(DeterministicRepair::source_backed_containers(
        repaired,
        Vec::new(),
        replacements,
    ))
}

fn append_referenced_container_dependency_closures(
    replacements: &mut Vec<ContainerReplacement>,
    code: &str,
    container_source: &str,
    source_index: &SourceIndex,
) {
    let mut referenced = Vec::new();
    for line in container_source.lines() {
        for identifier in identifiers_in_line(line) {
            if referenced.iter().any(|existing| existing == &identifier) {
                continue;
            }
            if source_index.container(&identifier).is_none() {
                continue;
            }
            if !container_needs_source_restore(code, &identifier) {
                continue;
            }
            referenced.push(identifier);
        }
    }
    referenced.sort();

    for identifier in referenced {
        for replacement in container_dependency_closure(&identifier, source_index) {
            if !container_needs_source_restore(code, &replacement.container_name) {
                continue;
            }
            if replacements
                .iter()
                .any(|existing| existing.container_name == replacement.container_name)
            {
                continue;
            }
            replacements.push(replacement);
        }
    }
}

fn container_needs_source_restore(code: &str, container_name: &str) -> bool {
    extract_container_from_source(code, container_name)
        .as_deref()
        .map(is_stub_like_container)
        .unwrap_or(true)
}

fn modifier_candidate_from_signature_line(line: &str) -> Option<String> {
    let trimmed = line.trim();
    let visibility = [" external ", " public ", " internal ", " private "]
        .iter()
        .find_map(|needle| trimmed.find(needle).map(|idx| idx + needle.len()))?;
    let tail = &trimmed[visibility..];
    let modifier_segment = tail.split(" returns").next().unwrap_or(tail);

    for token in modifier_segment.split_whitespace() {
        let candidate = token
            .split(|ch: char| !(ch.is_ascii_alphanumeric() || ch == '_'))
            .next()
            .unwrap_or("");
        if candidate.is_empty()
            || matches!(
                candidate,
                "payable" | "view" | "pure" | "virtual" | "override"
            )
        {
            continue;
        }
        return Some(candidate.to_string());
    }

    None
}

fn is_dangling_closing_call(trimmed: &str) -> bool {
    matches!(trimmed, ");" | ")" | ");," | "),")
}

fn synthetic_definition_for_symbol(symbol: &str) -> Option<&'static str> {
    match symbol {
        "ERC1155Holder" => Some(
            r#"abstract contract ERC1155Holder {
    function onERC1155Received(
        address,
        address,
        uint256,
        uint256,
        bytes memory
    ) public virtual returns (bytes4) {
        return this.onERC1155Received.selector;
    }

    function onERC1155BatchReceived(
        address,
        address,
        uint256[] memory,
        uint256[] memory,
        bytes memory
    ) public virtual returns (bytes4) {
        return this.onERC1155BatchReceived.selector;
    }
}"#,
        ),
        _ => None,
    }
}

fn is_base_precedence_error(err: &CompilerError) -> bool {
    err.code.as_deref() == Some("2449")
        || err
            .message
            .to_lowercase()
            .contains("definition of base has to precede definition of derived contract")
}

fn repair_base_precedence(code: &str, line_no: usize, original_source: &str) -> Option<String> {
    let lines: Vec<&str> = code.lines().collect();
    let derived_line = lines.get(line_no.saturating_sub(1))?.trim_start();
    let derived_name = parse_container_name(derived_line)?;
    let chunks = normalizer::split_top_level_chunks(code);
    let derived_idx = chunks
        .iter()
        .position(|chunk| normalizer::top_level_definition_names(chunk).contains(&derived_name))?;
    let base_names = parse_base_definition_names(&chunks[derived_idx]);
    if base_names.is_empty() {
        return None;
    }

    let mut moved_indices = std::collections::HashSet::new();
    let mut prefixes = Vec::new();

    for base_name in base_names {
        if let Some((idx, chunk)) = chunks
            .iter()
            .enumerate()
            .find(|(_, chunk)| normalizer::top_level_definition_names(chunk).contains(&base_name))
        {
            if idx > derived_idx {
                moved_indices.insert(idx);
                prefixes.push(chunk.clone());
            }
            continue;
        }

        if let Some(base_definition) =
            extract_top_level_definition_from_source(original_source, &base_name)
        {
            prefixes.push(base_definition);
        }
    }

    if prefixes.is_empty() {
        return None;
    }

    let mut repaired_chunks = Vec::new();
    for (idx, chunk) in chunks.into_iter().enumerate() {
        if moved_indices.contains(&idx) {
            continue;
        }
        if idx == derived_idx {
            repaired_chunks.extend(prefixes.clone());
        }
        repaired_chunks.push(chunk);
    }

    let repaired = repaired_chunks.join("\n\n");
    if stable_hash(&repaired) == stable_hash(code) {
        None
    } else {
        Some(repaired)
    }
}

fn replace_definition_containing_missing_symbol(
    code: &str,
    line_no: usize,
    column: Option<usize>,
    original_source: &str,
) -> Option<String> {
    let lines: Vec<&str> = code.lines().collect();
    let line = lines.get(line_no.saturating_sub(1))?;
    for symbol in missing_symbol_candidates(line, column) {
        if let Some(synthetic_definition) = synthetic_definition_for_symbol(&symbol) {
            if let Some(repaired) =
                insert_or_move_definition_before_line(code, &symbol, synthetic_definition, line_no)
            {
                return Some(repaired);
            }
        }

        let is_heavy = symbol_kind_in_source(original_source, &symbol)
            .map(|kind| {
                matches!(
                    kind,
                    "contract" | "abstract contract" | "interface" | "library"
                )
            })
            .unwrap_or(false);

        if !is_heavy {
            if let Some(original_definition) =
                extract_top_level_definition_from_source(original_source, &symbol)
            {
                if let Some(repaired) = insert_or_move_definition_before_line(
                    code,
                    &symbol,
                    &original_definition,
                    line_no,
                )
                .or_else(|| {
                    replace_top_level_definition_by_name(code, &symbol, &original_definition)
                }) {
                    let repaired = restore_referenced_named_type_definitions_for_line(
                        &repaired,
                        code,
                        line_no,
                        original_source,
                    )
                    .unwrap_or(repaired);
                    return Some(repaired);
                }
            }
        }

        let Some((container_name, original_container)) =
            extract_container_defining_symbol(original_source, &symbol)
        else {
            continue;
        };

        let container_is_heavy = symbol_kind_in_source(original_source, &container_name)
            .map(|kind| {
                matches!(
                    kind,
                    "contract" | "abstract contract" | "interface" | "library"
                )
            })
            .unwrap_or(false);

        if container_is_heavy {
            continue;
        }

        let Some(repaired) = replace_container_by_name(code, &container_name, &original_container)
        else {
            continue;
        };
        return Some(repaired);
    }

    None
}

fn restore_current_container_defining_missing_symbol(
    code: &str,
    line_no: usize,
    column: Option<usize>,
    original_source: &str,
) -> Option<DeterministicRepair> {
    let lines: Vec<&str> = code.lines().collect();
    let error_line = lines.get(line_no.saturating_sub(1))?;
    let current_container_start = find_enclosing_container_start(&lines, line_no)?;
    let current_container_end = find_block_end(&lines, current_container_start)?;
    let current_container = lines[current_container_start..=current_container_end].join("\n");
    let current_container_name = parse_container_name(lines[current_container_start].trim_start())?;
    let original_container =
        extract_container_from_source(original_source, &current_container_name)?;

    let original_is_manageable = original_container.lines().count() <= 500;
    let current_looks_like_harness = current_container.contains(" is Test")
        || current_container_name.ends_with("Test")
        || current_container_name == "PoC";
    if !original_is_manageable && !current_looks_like_harness {
        return None;
    }

    for symbol in missing_symbol_candidates(error_line, column) {
        if symbol == current_container_name {
            continue;
        }
        if container_defines_symbol(&original_container, &symbol) {
            if let Some(member_code) = extract_member_from_container(&original_container, &symbol) {
                if let Some(repaired) =
                    inject_into_container(code, &current_container_name, &member_code)
                {
                    let _kind = if member_code.trim_start().starts_with("function ") {
                        "function"
                    } else if member_code.trim_start().starts_with("modifier ") {
                        "modifier"
                    } else {
                        "variable"
                    };

                    let replacement = MissingSymbolRestoreAction::RestoreFunction {
                        container: current_container_name.clone(),
                        name: symbol.clone(),
                    }; // Using RestoreFunction broadly for now, can refine later

                    return Some(DeterministicRepair::missing_symbol_backed(
                        repaired,
                        vec![replacement],
                    ));
                }
            }
        }
    }

    None
}

fn restore_synthetic_test_support(
    code: &str,
    line_no: usize,
    column: Option<usize>,
) -> Option<String> {
    let lines: Vec<&str> = code.lines().collect();
    let error_line = lines.get(line_no.saturating_sub(1))?;
    let current_container_start = find_enclosing_container_start(&lines, line_no)?;
    let current_container_end = find_block_end(&lines, current_container_start)?;
    let current_container = lines[current_container_start..=current_container_end].join("\n");
    let base_names = parse_base_definition_names(&current_container);

    for symbol in missing_symbol_candidates(error_line, column) {
        if symbol == "console" {
            if let Some(repaired) =
                insert_or_replace_top_level_definition(code, "console", synthetic_console_library())
            {
                return Some(repaired);
            }
        }

        if is_test_support_symbol(&symbol) && base_names.iter().any(|base| base == "Test") {
            if let Some(repaired) =
                insert_or_replace_top_level_definition(code, "Test", synthetic_test_contract())
            {
                return Some(repaired);
            }
        }
    }

    None
}

fn restore_container_for_missing_member(
    code: &str,
    err: &CompilerError,
    original_source: &str,
) -> Option<DeterministicRepair> {
    let (container_name, member_name) = missing_member_provider_from_message(&err.message)?;
    let original_container = extract_container_from_source(original_source, &container_name)?;
    if !container_defines_symbol(&original_container, &member_name) {
        return None;
    }

    let existing_container = extract_container_from_source(code, &container_name);

    if existing_container.is_some() {
        if let Some(member_code) = extract_member_from_container(&original_container, &member_name)
        {
            if let Some(repaired) = inject_into_container(code, &container_name, &member_code) {
                let replacement = MissingSymbolRestoreAction::RestoreFunction {
                    container: container_name.clone(),
                    name: member_name.clone(),
                };
                return Some(DeterministicRepair::missing_symbol_backed(
                    repaired,
                    vec![replacement],
                ));
            }
        }
    }

    let repaired =
        replace_top_level_definition_by_name(code, &container_name, &original_container)?;
    Some(DeterministicRepair::source_backed_containers(
        repaired,
        Vec::new(),
        vec![ContainerReplacement {
            container_name,
            expected_hash: stable_hash(&original_container),
        }],
    ))
}

fn restore_extension_provider_for_missing_member(
    code: &str,
    err: &CompilerError,
    source_index: &SourceIndex,
) -> Option<DeterministicRepair> {
    let member_name = missing_member_name_from_message(&err.message)?;
    let providers = source_index.providers_for_symbol(&member_name);

    for provider in providers {
        let source_container = source_index.container(&provider)?;
        let current_container = extract_container_from_source(code, &provider);
        let current_is_missing_or_stub = current_container
            .as_deref()
            .map(is_stub_like_container)
            .unwrap_or(true);
        if !current_is_missing_or_stub && source_container.source.lines().count() > 220 {
            continue;
        }

        if current_container.is_some() {
            if let Some(member_code) =
                extract_member_from_container(&source_container.source, &member_name)
            {
                if let Some(repaired) = inject_into_container(code, &provider, &member_code) {
                    let replacement = MissingSymbolRestoreAction::RestoreFunction {
                        container: provider.clone(),
                        name: member_name.clone(),
                    };
                    return Some(DeterministicRepair::missing_symbol_backed(
                        repaired,
                        vec![replacement],
                    ));
                }
            }
        }

        let Some(repaired) =
            replace_top_level_definition_by_name(code, &provider, &source_container.source)
        else {
            continue;
        };
        return Some(DeterministicRepair::source_backed_containers(
            repaired,
            Vec::new(),
            vec![ContainerReplacement {
                container_name: provider,
                expected_hash: source_container.body_hash,
            }],
        ));
    }

    None
}

fn restore_missing_top_level_provider(
    code: &str,
    line_no: usize,
    column: Option<usize>,
    source_index: &SourceIndex,
) -> Option<DeterministicRepair> {
    let lines: Vec<&str> = code.lines().collect();
    let error_line = lines.get(line_no.saturating_sub(1))?;

    for symbol in missing_symbol_candidates(error_line, column) {
        let Some(source_container) = source_index.container(&symbol) else {
            continue;
        };
        if !matches!(
            source_container.kind.as_str(),
            "library" | "interface" | "contract" | "abstract contract"
        ) {
            continue;
        }

        let current_container = extract_container_from_source(code, &symbol);
        let current_is_missing_or_stub = current_container
            .as_deref()
            .map(is_stub_like_container)
            .unwrap_or(true);
        if !current_is_missing_or_stub && source_container.source.lines().count() > 220 {
            continue;
        }

        let Some(mut repaired) =
            insert_or_move_definition_before_line(code, &symbol, &source_container.source, line_no)
                .or_else(|| {
                    replace_top_level_definition_by_name(code, &symbol, &source_container.source)
                })
        else {
            continue;
        };
        let mut replacements = vec![ContainerReplacement {
            container_name: symbol,
            expected_hash: source_container.body_hash,
        }];

        if let Some(current_container_start) = find_enclosing_container_start(&lines, line_no) {
            if let Some(current_container_end) = find_block_end(&lines, current_container_start) {
                let current_container =
                    lines[current_container_start..=current_container_end].join("\n");
                let current_container_name =
                    parse_container_name(lines[current_container_start].trim_start());
                if !is_test_support_dependency_expansion_container(
                    current_container_name.as_deref(),
                    &current_container,
                ) {
                    append_referenced_container_dependency_closures(
                        &mut replacements,
                        code,
                        &current_container,
                        source_index,
                    );
                }
            }
        }

        let mut applied_replacements = Vec::new();
        applied_replacements.push(replacements[0].clone());
        for replacement in replacements.iter().skip(1) {
            if let Some(next) =
                replace_container_by_source_target(&repaired, replacement, source_index)
            {
                repaired = next;
                applied_replacements.push(replacement.clone());
            }
        }

        return Some(DeterministicRepair::source_backed_containers(
            repaired,
            Vec::new(),
            applied_replacements,
        ));
    }

    None
}

fn is_test_support_dependency_expansion_container(
    container_name: Option<&str>,
    container_source: &str,
) -> bool {
    let name = container_name.unwrap_or("");
    name == "PoC"
        || name == "Test"
        || name == "CommonBase"
        || name == "Vm"
        || name == "VmSafe"
        || name.ends_with("Test")
        || name.starts_with("Std")
        || container_source.contains(" is Test")
        || container_source.contains("Vm internal constant")
}

fn restore_using_library_from_source(
    code: &str,
    line_no: usize,
    source_index: &SourceIndex,
) -> Option<DeterministicRepair> {
    let lines: Vec<&str> = code.lines().collect();
    let line = lines.get(line_no.saturating_sub(1))?;
    let library_name = parse_using_library_name(line)?;
    let source_container = source_index.container(&library_name)?;
    if source_container.kind != "library" {
        return None;
    }

    let replacements = container_dependency_closure(&library_name, source_index);
    let mut repaired = code.to_string();
    for replacement in &replacements {
        repaired = replace_container_by_source_target(&repaired, replacement, source_index)?;
    }

    Some(DeterministicRepair::source_backed_containers(
        repaired,
        Vec::new(),
        replacements,
    ))
}

fn try_restore_using_libraries_from_errors(
    code: &str,
    errors: &[CompilerError],
    source_index: &SourceIndex,
) -> Option<DeterministicRepair> {
    for err in errors {
        if !is_identifier_not_library_name_error(err) {
            continue;
        }
        let Some(library_name) = using_library_name_for_error(code, err, source_index) else {
            continue;
        };
        let replacements = library_dependency_closure(&library_name, source_index);
        if replacements.is_empty() {
            println!(
                "    -> Found using-library error for {}, but no source closure was indexed.",
                library_name
            );
            continue;
        }

        let mut repaired = code.to_string();
        for replacement in &replacements {
            if let Some(next) =
                replace_container_by_source_target(&repaired, replacement, source_index)
            {
                repaired = next;
            }
        }
        if repaired == code {
            continue;
        }
        println!(
            "    -> Restored using-library dependency closure: {}.",
            replacements
                .iter()
                .map(|replacement| replacement.container_name.as_str())
                .collect::<Vec<_>>()
                .join(", ")
        );
        return Some(DeterministicRepair::source_backed_containers(
            repaired,
            Vec::new(),
            replacements,
        ));
    }

    None
}

fn using_library_name_for_error(
    code: &str,
    err: &CompilerError,
    _source_index: &SourceIndex,
) -> Option<String> {
    for snippet_line in &err.snippet {
        if let Some(name) = parse_using_library_name_from_text(snippet_line) {
            return Some(name);
        }
    }

    let lines: Vec<&str> = code.lines().collect();
    let line_no = err.line?;
    let start = line_no.saturating_sub(6);
    let end = (line_no + 5).min(lines.len());
    for line in &lines[start..end] {
        if let Some(name) = parse_using_library_name_from_text(line) {
            return Some(name);
        }
    }
    for line in &lines {
        let Some(name) = parse_using_library_name_from_text(line) else {
            continue;
        };
        return Some(name);
    }
    None
}

fn container_dependency_closure(
    container_name: &str,
    source_index: &SourceIndex,
) -> Vec<ContainerReplacement> {
    let mut seen = HashSet::new();
    let mut replacements = Vec::new();
    collect_container_dependency_closure(
        container_name,
        source_index,
        &mut seen,
        &mut replacements,
    );
    replacements
}

fn library_dependency_closure(
    library_name: &str,
    source_index: &SourceIndex,
) -> Vec<ContainerReplacement> {
    let mut seen = HashSet::new();
    let mut replacements = Vec::new();
    collect_library_dependency_closure(library_name, source_index, &mut seen, &mut replacements);
    replacements
}

fn collect_library_dependency_closure(
    library_name: &str,
    source_index: &SourceIndex,
    seen: &mut HashSet<String>,
    replacements: &mut Vec<ContainerReplacement>,
) {
    if !seen.insert(library_name.to_string()) {
        return;
    }
    let Some(source_container) = source_index.container(library_name) else {
        return;
    };
    if source_container.kind != "library" {
        return;
    }

    let mut dependencies = Vec::new();
    for line in source_container.source.lines() {
        for identifier in identifiers_in_line(line) {
            if identifier == library_name || dependencies.iter().any(|name| name == &identifier) {
                continue;
            }
            if source_index
                .container(&identifier)
                .map(|container| container.kind == "library")
                .unwrap_or(false)
            {
                dependencies.push(identifier);
            }
        }
    }
    dependencies.sort();

    for dependency in dependencies {
        collect_library_dependency_closure(&dependency, source_index, seen, replacements);
    }
    replacements.push(ContainerReplacement {
        container_name: library_name.to_string(),
        expected_hash: source_container.body_hash,
    });
}

fn collect_container_dependency_closure(
    container_name: &str,
    source_index: &SourceIndex,
    seen: &mut HashSet<String>,
    replacements: &mut Vec<ContainerReplacement>,
) {
    if !seen.insert(container_name.to_string()) {
        return;
    }
    let Some(source_container) = source_index.container(container_name) else {
        return;
    };

    let mut dependencies = Vec::new();
    for line in source_container.source.lines() {
        for identifier in identifiers_in_line(line) {
            if identifier == container_name || dependencies.iter().any(|name| name == &identifier) {
                continue;
            }
            if source_index.container(&identifier).is_some() {
                dependencies.push(identifier);
            }
        }
    }
    dependencies.sort();

    for dependency in dependencies {
        collect_container_dependency_closure(&dependency, source_index, seen, replacements);
    }
    replacements.push(ContainerReplacement {
        container_name: container_name.to_string(),
        expected_hash: source_container.body_hash,
    });
}

fn parse_using_library_name(line: &str) -> Option<String> {
    let trimmed = line.trim();
    let rest = trimmed.strip_prefix("using ")?;
    let library_name = rest.split(" for ").next()?.trim();
    if library_name.is_empty()
        || library_name.starts_with('{')
        || library_name
            .chars()
            .any(|ch| !(ch == '_' || ch.is_ascii_alphanumeric()))
    {
        return None;
    }
    Some(library_name.to_string())
}

fn parse_using_library_name_from_text(text: &str) -> Option<String> {
    let idx = text.find("using ")?;
    parse_using_library_name(&text[idx..])
}

fn missing_member_provider_from_message(message: &str) -> Option<(String, String)> {
    let member_name = missing_member_name_from_message(message)?;

    for marker in ["type(library ", "type(contract ", "type(interface "] {
        let Some(container_start) = message.find(marker).map(|idx| idx + marker.len()) else {
            continue;
        };
        let container_tail = &message[container_start..];
        let container_end = container_tail.find(')')?;
        let container_name = container_tail[..container_end].trim();
        if !container_name.is_empty() {
            return Some((container_name.to_string(), member_name));
        }
    }

    for marker in ["in contract ", "in library ", "in interface "] {
        let Some(container_start) = message.find(marker).map(|idx| idx + marker.len()) else {
            continue;
        };
        let container_tail = &message[container_start..];
        let container_name = container_tail
            .split(|ch: char| !(ch == '_' || ch.is_ascii_alphanumeric()))
            .next()
            .unwrap_or("")
            .trim();
        if !container_name.is_empty() {
            return Some((container_name.to_string(), member_name));
        }
    }

    None
}

fn missing_member_name_from_message(message: &str) -> Option<String> {
    let member_start = message.find("Member \"")? + "Member \"".len();
    let member_tail = &message[member_start..];
    let member_end = member_tail.find('"')?;
    Some(member_tail[..member_end].to_string())
}

fn insert_or_replace_top_level_definition(
    code: &str,
    definition_name: &str,
    replacement: &str,
) -> Option<String> {
    replace_top_level_definition_by_name(code, definition_name, replacement)
}

fn is_test_support_symbol(symbol: &str) -> bool {
    matches!(
        symbol,
        "vm" | "assertEq" | "assertGt" | "assertLt" | "assertTrue" | "assertFalse"
    )
}

fn synthetic_console_library() -> &'static str {
    r#"library console {
    function log(string memory) internal pure {}
    function log(string memory, uint256) internal pure {}
    function log(string memory, int256) internal pure {}
    function log(string memory, address) internal pure {}
    function log(string memory, bool) internal pure {}
    function log(string memory, uint256, string memory) internal pure {}
}"#
}

fn synthetic_test_contract() -> &'static str {
    r#"interface Vm {
    function prank(address) external;
    function startPrank(address) external;
    function stopPrank() external;
}

abstract contract Test {
    Vm public constant vm = Vm(address(uint160(0x7109709ECfa91a80626fF3989D68f67F5b1DD12D)));

    function assertEq(uint256, uint256) internal pure virtual {}
    function assertEq(uint256, uint256, string memory) internal pure virtual {}
    function assertEq(address, address) internal pure virtual {}
    function assertEq(address, address, string memory) internal pure virtual {}
    function assertEq(bool, bool) internal pure virtual {}
    function assertEq(bool, bool, string memory) internal pure virtual {}
    function assertGt(uint256, uint256) internal pure virtual {}
    function assertGt(uint256, uint256, string memory) internal pure virtual {}
    function assertLt(uint256, uint256) internal pure virtual {}
    function assertLt(uint256, uint256, string memory) internal pure virtual {}
    function assertTrue(bool) internal pure virtual {}
    function assertFalse(bool) internal pure virtual {}
}"#
}

fn restore_base_container_defining_missing_symbol(
    code: &str,
    line_no: usize,
    column: Option<usize>,
    original_source: &str,
) -> Option<DeterministicRepair> {
    let lines: Vec<&str> = code.lines().collect();
    let error_line = lines.get(line_no.saturating_sub(1))?;
    let current_container_start = find_enclosing_container_start(&lines, line_no)?;
    let current_container_end = find_block_end(&lines, current_container_start)?;
    let current_container = lines[current_container_start..=current_container_end].join("\n");
    let base_names = parse_base_definition_names(&current_container);
    if base_names.is_empty() {
        return None;
    }

    for symbol in missing_symbol_candidates(error_line, column) {
        let Some((provider_name, original_container)) =
            extract_allowed_container_defining_symbol(original_source, &symbol, &base_names)
        else {
            continue;
        };

        let existing_provider = extract_container_from_source(code, &provider_name);

        if existing_provider.is_some() {
            if let Some(member_code) = extract_member_from_container(&original_container, &symbol) {
                if let Some(repaired) = inject_into_container(code, &provider_name, &member_code) {
                    let replacement = MissingSymbolRestoreAction::RestoreFunction {
                        container: provider_name.clone(),
                        name: symbol.clone(),
                    };
                    return Some(DeterministicRepair::missing_symbol_backed(
                        repaired,
                        vec![replacement],
                    ));
                }
            }
        }

        let existing_is_stub = existing_provider
            .as_deref()
            .map(is_stub_like_container)
            .unwrap_or(false);
        let original_is_small = original_container.lines().count() <= 180;

        if !existing_is_stub && !original_is_small {
            continue;
        }

        if let Some(repaired) =
            replace_top_level_definition_by_name(code, &provider_name, &original_container)
        {
            let replacement = ContainerReplacement {
                container_name: provider_name.clone(),
                expected_hash: stable_hash(&original_container),
            };
            return Some(DeterministicRepair::source_backed_containers(
                repaired,
                vec![],
                vec![replacement],
            ));
        }
    }

    None
}

fn restore_referenced_named_type_definitions_for_line(
    repaired: &str,
    original_code: &str,
    line_no: usize,
    original_source: &str,
) -> Option<String> {
    let lines: Vec<&str> = original_code.lines().collect();
    let current_container_start = find_enclosing_container_start(&lines, line_no)?;
    let current_container_end = find_block_end(&lines, current_container_start)?;
    let current_container = lines[current_container_start..=current_container_end].join("\n");
    let named_type_definitions = collect_top_level_type_definition_names(original_source);
    let mut referenced = Vec::new();

    for line in current_container.lines() {
        for identifier in identifiers_in_line(line) {
            if !named_type_definitions.contains(&identifier) {
                continue;
            }
            if referenced.iter().any(|existing| existing == &identifier) {
                continue;
            }
            if top_level_definition_kind_in_code(repaired, &identifier).is_some() {
                continue;
            }
            referenced.push(identifier);
        }
    }
    referenced.sort();

    let mut current = repaired.to_string();
    let mut changed = false;
    for identifier in referenced {
        let Some(definition) =
            extract_top_level_definition_from_source(original_source, &identifier)
        else {
            continue;
        };
        if let Some(next) = replace_top_level_definition_by_name(&current, &identifier, &definition)
        {
            current = next;
            changed = true;
        }
    }

    changed.then_some(current)
}

fn is_stub_like_container(container: &str) -> bool {
    let meaningful_lines = container
        .lines()
        .map(str::trim)
        .filter(|line| {
            !line.is_empty()
                && !line.starts_with("//")
                && !line.starts_with("/*")
                && !line.starts_with('*')
        })
        .count();

    meaningful_lines <= 6
        || (container.contains("modifier onlyOwner()")
            && !container.contains("function ")
            && !container.contains("constructor("))
}

fn symbol_kind_in_source(source: &str, name: &str) -> Option<&'static str> {
    for line in source.lines() {
        if let Some((kind, found_name)) = normalizer::parse_top_level_definition(line.trim_start())
        {
            if found_name == name {
                return Some(kind);
            }
        }
    }
    None
}

fn extract_top_level_definition_from_source(source: &str, name: &str) -> Option<String> {
    let named_type_definitions = collect_top_level_type_definition_names(source);
    extract_top_level_definition_with_dependencies(
        source,
        name,
        &named_type_definitions,
        &mut std::collections::HashSet::new(),
    )
}

fn extract_top_level_definition_with_dependencies(
    source: &str,
    name: &str,
    named_type_definitions: &std::collections::HashSet<String>,
    seen: &mut std::collections::HashSet<String>,
) -> Option<String> {
    if !seen.insert(name.to_string()) {
        return None;
    }

    let definition = extract_top_level_definition_by_scan(source, name).or_else(|| {
        normalizer::split_top_level_chunks(source)
            .into_iter()
            .find(|chunk| normalizer::top_level_definition_names(chunk).contains(name))
    })?;

    let mut parts = Vec::new();
    for base in parse_base_definition_names(&definition) {
        if let Some(base_definition) = extract_top_level_definition_with_dependencies(
            source,
            &base,
            named_type_definitions,
            seen,
        ) {
            parts.push(base_definition);
        }
    }
    for dependency in referenced_named_type_definitions(&definition, named_type_definitions) {
        if dependency == name {
            continue;
        }
        if let Some(dependency_definition) = extract_top_level_definition_with_dependencies(
            source,
            &dependency,
            named_type_definitions,
            seen,
        ) {
            parts.push(dependency_definition);
        }
    }
    parts.push(definition);

    Some(parts.join("\n\n"))
}

fn collect_top_level_type_definition_names(source: &str) -> std::collections::HashSet<String> {
    let mut names = std::collections::HashSet::new();
    let mut tracker = DepthTracker::default();

    for line in source.lines() {
        if tracker.depth == 0 {
            if let Some((kind, name)) = normalizer::parse_top_level_definition(line.trim_start()) {
                if matches!(kind, "type" | "struct" | "enum") {
                    names.insert(name.to_string());
                }
            }
        }

        tracker.process_line_and_check_end(line);
    }

    names
}

fn referenced_named_type_definitions(
    definition: &str,
    named_type_definitions: &std::collections::HashSet<String>,
) -> Vec<String> {
    let mut dependencies = Vec::new();

    for symbol in identifiers_in_line(definition) {
        if named_type_definitions.contains(&symbol)
            && !dependencies
                .iter()
                .any(|existing: &String| existing == &symbol)
        {
            dependencies.push(symbol);
        }
    }

    dependencies
}

fn extract_top_level_definition_by_scan(source: &str, name: &str) -> Option<String> {
    let lines: Vec<&str> = source.lines().collect();
    let mut tracker = DepthTracker::default();
    for (idx, line) in lines.iter().enumerate() {
        let trimmed = line.trim_start();
        let parsed = normalizer::parse_top_level_definition(trimmed);
        let is_major_container = parsed
            .map(|(kind, _)| {
                matches!(
                    kind,
                    "contract" | "abstract contract" | "interface" | "library"
                )
            })
            .unwrap_or(false);

        if parsed.map(|(_, found)| found) != Some(name)
            || (tracker.depth != 0 && !is_major_container)
        {
            tracker.process_line_and_check_end(line);
            continue;
        }

        if trimmed.ends_with(';') {
            return Some(lines[idx].to_string());
        }

        let end = find_block_end(&lines, idx)?;
        return Some(lines[idx..=end].join("\n"));
    }

    None
}

fn parse_base_definition_names(definition: &str) -> Vec<String> {
    let mut header = String::new();
    for line in definition.lines().take(20) {
        header.push(' ');
        header.push_str(line.trim());
        if line.contains('{') || line.trim_end().ends_with(';') {
            break;
        }
    }

    let Some((_, bases)) = header.split_once(" is ") else {
        return Vec::new();
    };
    let bases = bases
        .split('{')
        .next()
        .or_else(|| bases.split(';').next())
        .unwrap_or(bases);

    bases
        .split(',')
        .filter_map(|base| {
            let name = base
                .trim()
                .split(|ch: char| !(ch.is_ascii_alphanumeric() || ch == '_'))
                .next()
                .unwrap_or("");
            if name.is_empty() {
                None
            } else {
                Some(name.to_string())
            }
        })
        .collect()
}

fn identifier_at_column(line: &str, column: usize) -> Option<String> {
    let bytes = line.as_bytes();
    if bytes.is_empty() {
        return None;
    }

    let mut idx = column.saturating_sub(1).min(bytes.len().saturating_sub(1));
    if !is_identifier_byte(bytes[idx]) {
        if idx > 0 && is_identifier_byte(bytes[idx - 1]) {
            idx -= 1;
        } else {
            return None;
        }
    }

    let mut start = idx;
    while start > 0 && is_identifier_byte(bytes[start - 1]) {
        start -= 1;
    }

    let mut end = idx + 1;
    while end < bytes.len() && is_identifier_byte(bytes[end]) {
        end += 1;
    }

    let symbol = &line[start..end];
    if symbol.is_empty() {
        None
    } else {
        Some(symbol.to_string())
    }
}

fn missing_symbol_candidates(line: &str, column: Option<usize>) -> Vec<String> {
    let mut candidates = Vec::new();
    let mut has_column_candidate = false;

    if let Some(receiver) = dotted_receiver_candidate(line, column) {
        candidates.push(receiver);
        has_column_candidate = true;
    } else if let Some(column) = column {
        if let Some(symbol) = identifier_at_column(line, column) {
            candidates.push(symbol);
            has_column_candidate = true;
        }
    }

    let mut fallback = Vec::new();
    for symbol in identifiers_in_line(line) {
        if !candidates.iter().any(|candidate| candidate == &symbol) {
            fallback.push(symbol);
        }
    }

    fallback.sort_by_key(|symbol| symbol_priority(symbol));
    if !has_column_candidate {
        candidates = fallback;
    }
    candidates
}

fn dotted_receiver_candidate(line: &str, column: Option<usize>) -> Option<String> {
    let column = column?;
    let bytes = line.as_bytes();
    if bytes.is_empty() {
        return None;
    }
    let mut idx = column.saturating_sub(1).min(bytes.len().saturating_sub(1));
    while idx < bytes.len() && is_identifier_byte(bytes[idx]) {
        idx += 1;
    }
    if bytes.get(idx) != Some(&b'.') {
        return None;
    }
    let mut start = column.saturating_sub(1).min(bytes.len().saturating_sub(1));
    while start > 0 && is_identifier_byte(bytes[start - 1]) {
        start -= 1;
    }
    let receiver = &line[start..idx];
    if receiver.is_empty() {
        None
    } else {
        Some(receiver.to_string())
    }
}

fn identifiers_in_line(line: &str) -> Vec<String> {
    let bytes = line.as_bytes();
    let mut out = Vec::new();
    let mut idx = 0usize;

    while idx < bytes.len() {
        if !is_identifier_byte(bytes[idx]) || bytes[idx].is_ascii_digit() {
            idx += 1;
            continue;
        }

        let start = idx;
        idx += 1;
        while idx < bytes.len() && is_identifier_byte(bytes[idx]) {
            idx += 1;
        }

        let symbol = &line[start..idx];
        if !is_solidity_keyword(symbol) && !out.iter().any(|existing| existing == symbol) {
            out.push(symbol.to_string());
        }
    }

    out
}

fn symbol_priority(symbol: &str) -> u8 {
    if symbol.starts_with('_') {
        0
    } else if symbol
        .chars()
        .next()
        .map(|ch| ch.is_ascii_uppercase())
        .unwrap_or(false)
    {
        1
    } else {
        2
    }
}

fn is_solidity_keyword(symbol: &str) -> bool {
    matches!(
        symbol,
        "return"
            | "if"
            | "else"
            | "for"
            | "while"
            | "uint256"
            | "uint128"
            | "uint64"
            | "uint32"
            | "uint24"
            | "uint16"
            | "uint8"
            | "int256"
            | "int128"
            | "address"
            | "bool"
            | "true"
            | "false"
            | "type"
            | "new"
    )
}

fn is_identifier_byte(byte: u8) -> bool {
    byte.is_ascii_alphanumeric() || byte == b'_'
}

fn is_identifier(symbol: &str) -> bool {
    let mut chars = symbol.chars();
    let Some(first) = chars.next() else {
        return false;
    };
    (first.is_ascii_alphabetic() || first == '_')
        && chars.all(|ch| ch.is_ascii_alphanumeric() || ch == '_')
}

fn extract_container_defining_symbol(source: &str, symbol: &str) -> Option<(String, String)> {
    let lines: Vec<&str> = source.lines().collect();
    let mut idx = 0usize;

    while idx < lines.len() {
        let trimmed = lines[idx].trim_start();
        let Some(container_name) = parse_container_name(trimmed) else {
            idx += 1;
            continue;
        };
        let Some(end) = find_block_end(&lines, idx) else {
            idx += 1;
            continue;
        };
        let container = lines[idx..=end].join("\n");
        if container_defines_symbol(&container, symbol) {
            return Some((container_name, container));
        }
        idx = end + 1;
    }

    None
}

fn extract_allowed_container_defining_symbol(
    source: &str,
    symbol: &str,
    allowed_names: &[String],
) -> Option<(String, String)> {
    let lines: Vec<&str> = source.lines().collect();
    let mut idx = 0usize;

    while idx < lines.len() {
        let trimmed = lines[idx].trim_start();
        let Some(container_name) = parse_container_name(trimmed) else {
            idx += 1;
            continue;
        };
        let Some(end) = find_block_end(&lines, idx) else {
            idx += 1;
            continue;
        };

        if allowed_names.iter().any(|name| name == &container_name) {
            let container = lines[idx..=end].join("\n");
            if container_defines_symbol(&container, symbol) {
                return Some((container_name, container));
            }
        }

        idx = end + 1;
    }

    None
}

fn extract_member_from_container(container: &str, symbol: &str) -> Option<String> {
    let lines: Vec<&str> = container.lines().collect();
    let mut tracker = DepthTracker::default();

    for (idx, line) in lines.iter().enumerate() {
        if tracker.depth == 1 && declares_identifier(line, symbol) {
            let trimmed = line.trim_start();
            if trimmed.starts_with("function ") || trimmed.starts_with("modifier ") {
                let end = find_function_end(&lines, idx)?;
                return Some(lines[idx..=end].join("\n"));
            } else if trimmed.contains("{") && !trimmed.ends_with(';') {
                let end = find_block_end(&lines, idx)?;
                return Some(lines[idx..=end].join("\n"));
            } else {
                return Some(line.to_string());
            }
        }

        tracker.process_line_and_check_end(line);
    }
    None
}

fn container_defines_symbol(container: &str, symbol: &str) -> bool {
    let mut tracker = DepthTracker::default();
    for line in container.lines() {
        if tracker.depth == 1 && declares_identifier(line, symbol) {
            return true;
        }

        tracker.process_line_and_check_end(line);
    }

    false
}

fn declares_identifier(line: &str, symbol: &str) -> bool {
    let trimmed = line.trim_start();
    if trimmed.starts_with("//")
        || trimmed.starts_with('*')
        || trimmed.starts_with("/*")
        || trimmed.starts_with("return ")
    {
        return false;
    }

    let function_pattern = format!("function {}(", symbol);
    if trimmed.starts_with(&function_pattern) {
        return true;
    }
    let modifier_pattern = format!("modifier {}(", symbol);
    if trimmed.starts_with(&modifier_pattern) {
        return true;
    }
    let event_pattern = format!("event {}(", symbol);
    if trimmed.starts_with(&event_pattern) {
        return true;
    }

    if !trimmed.ends_with(';') {
        return false;
    }

    contains_identifier(trimmed, symbol)
        && (trimmed.contains(" public ")
            || trimmed.contains(" internal ")
            || trimmed.contains(" private ")
            || trimmed.contains(" constant ")
            || trimmed.contains(" immutable ")
            || trimmed.starts_with("mapping(")
            || trimmed.starts_with("uint")
            || trimmed.starts_with("int")
            || trimmed.starts_with("address ")
            || trimmed.starts_with("bool ")
            || trimmed.starts_with("bytes"))
}

fn contains_identifier(text: &str, symbol: &str) -> bool {
    let mut search_start = 0usize;
    while let Some(pos) = text[search_start..].find(symbol) {
        let start = search_start + pos;
        let end = start + symbol.len();
        let before = start
            .checked_sub(1)
            .and_then(|idx| text.as_bytes().get(idx))
            .copied();
        let after = text.as_bytes().get(end).copied();
        let before_ok = before.map(|byte| !is_identifier_byte(byte)).unwrap_or(true);
        let after_ok = after.map(|byte| !is_identifier_byte(byte)).unwrap_or(true);
        if before_ok && after_ok {
            return true;
        }
        search_start = end;
    }
    false
}

fn insert_or_move_definition_before_line(
    code: &str,
    definition_name: &str,
    replacement: &str,
    line_no: usize,
) -> Option<String> {
    let chunks = split_top_level_chunks_with_spans(code);
    if chunks.is_empty() {
        return None;
    }

    let lines: Vec<&str> = code.lines().collect();
    let anchor_line = find_enclosing_container_start(&lines, line_no)
        .unwrap_or_else(|| line_no.saturating_sub(1))
        .saturating_add(1);
    let anchor_idx = chunks
        .iter()
        .position(|chunk| anchor_line >= chunk.start_line && anchor_line <= chunk.end_line)
        .unwrap_or(0);
    let existing_idx = chunks.iter().position(|chunk| {
        normalizer::top_level_definition_names(&chunk.text).contains(definition_name)
    });

    if existing_idx.is_some_and(|idx| idx < anchor_idx) {
        return None;
    }

    let mut repaired_chunks = Vec::new();
    for (idx, chunk) in chunks.iter().enumerate() {
        if existing_idx == Some(idx) {
            continue;
        }
        if idx == anchor_idx {
            repaired_chunks.push(replacement.to_string());
        }
        repaired_chunks.push(chunk.text.clone());
    }

    let repaired = repaired_chunks.join("\n\n");
    if normalizer::normalize_solidity_fragment(&repaired)
        == normalizer::normalize_solidity_fragment(code)
    {
        None
    } else {
        Some(repaired)
    }
}

#[derive(Debug, Clone)]
struct TopLevelChunk {
    start_line: usize,
    end_line: usize,
    text: String,
}

fn split_top_level_chunks_with_spans(code: &str) -> Vec<TopLevelChunk> {
    let mut chunks = Vec::new();
    let mut current = Vec::new();
    let mut current_start = 1usize;
    let mut tracker = DepthTracker::default();

    for (idx, line) in code.lines().enumerate() {
        let line_no = idx + 1;
        let trimmed = line.trim_start();
        let starts_top_level_item =
            tracker.depth == 0 && normalizer::parse_top_level_definition(trimmed).is_some();

        if starts_top_level_item && !current.is_empty() {
            chunks.push(TopLevelChunk {
                start_line: current_start,
                end_line: line_no - 1,
                text: current.join("\n"),
            });
            current.clear();
            current_start = line_no;
        }

        if current.is_empty() {
            current_start = line_no;
        }
        current.push(line.to_string());

        tracker.process_line_and_check_end(line);

        if tracker.depth == 0
            && !current.is_empty()
            && (trimmed.starts_with("type ") || trimmed.starts_with("error "))
            && trimmed.ends_with(';')
        {
            chunks.push(TopLevelChunk {
                start_line: current_start,
                end_line: line_no,
                text: current.join("\n"),
            });
            current.clear();
        }
    }

    if !current.is_empty() {
        chunks.push(TopLevelChunk {
            start_line: current_start,
            end_line: code.lines().count(),
            text: current.join("\n"),
        });
    }

    chunks
}

fn replace_container_by_name(
    code: &str,
    container_name: &str,
    replacement: &str,
) -> Option<String> {
    replace_top_level_definition_by_name(code, container_name, replacement)
}

fn replace_top_level_definition_by_name(
    code: &str,
    definition_name: &str,
    replacement: &str,
) -> Option<String> {
    let mut replaced = false;
    let mut repaired_chunks = Vec::new();

    for chunk in normalizer::split_top_level_chunks(code) {
        if normalizer::top_level_definition_names(&chunk).contains(definition_name) {
            repaired_chunks.push(replacement.to_string());
            replaced = true;
        } else {
            repaired_chunks.push(chunk);
        }
    }

    let repaired = if replaced {
        repaired_chunks.join("\n\n")
    } else {
        format!("{}\n\n{}", replacement, code)
    };

    if normalizer::normalize_solidity_fragment(&repaired)
        == normalizer::normalize_solidity_fragment(code)
    {
        None
    } else {
        Some(repaired)
    }
}

fn top_level_definition_kind_in_code(code: &str, definition_name: &str) -> Option<String> {
    for chunk in normalizer::split_top_level_chunks(code) {
        if !normalizer::top_level_definition_names(&chunk).contains(definition_name) {
            continue;
        }
        for line in chunk.lines() {
            if let Some((kind, name)) = normalizer::parse_top_level_definition(line.trim_start()) {
                if name == definition_name {
                    return Some(kind.to_string());
                }
            }
        }
    }

    None
}

fn replace_enclosing_container_from_source(
    code: &str,
    line_no: usize,
    original_source: &str,
) -> Option<String> {
    let lines: Vec<&str> = code.lines().collect();
    let container_start = match find_enclosing_container_start(&lines, line_no) {
        Some(start) => start,
        None => {
            println!("    -> Could not find enclosing top-level definition.");
            return None;
        }
    };
    let container_name = match parse_container_name(lines.get(container_start)?.trim_start()) {
        Some(name) => name,
        None => {
            println!("    -> Could not parse enclosing top-level definition name.");
            return None;
        }
    };

    let is_heavy = symbol_kind_in_source(original_source, &container_name)
        .map(|kind| {
            matches!(
                kind,
                "contract" | "abstract contract" | "interface" | "library"
            )
        })
        .unwrap_or(false);

    if is_heavy {
        return None;
    }
    let container_end = match find_block_end(&lines, container_start) {
        Some(end) => end,
        None => {
            println!(
                "    -> Could not find end for top-level definition {}.",
                container_name
            );
            return None;
        }
    };
    let original_container = match extract_container_from_source(original_source, &container_name) {
        Some(container) => container,
        None => {
            println!(
                "    -> Could not extract original top-level definition {} from source.",
                container_name
            );
            return None;
        }
    };

    let mut repaired = Vec::new();
    for line in lines.iter().take(container_start) {
        repaired.push((*line).to_string());
    }
    repaired.push(original_container);
    for line in lines.iter().skip(container_end + 1) {
        repaired.push((*line).to_string());
    }

    Some(repaired.join("\n"))
}

fn replace_enclosing_container_everywhere_from_source(
    code: &str,
    line_no: usize,
    original_source: &str,
) -> Option<String> {
    let lines: Vec<&str> = code.lines().collect();
    let container_start = match find_enclosing_container_start(&lines, line_no) {
        Some(start) => start,
        None => {
            println!("    -> Could not find enclosing top-level definition.");
            return None;
        }
    };
    let container_name = match parse_container_name(lines.get(container_start)?.trim_start()) {
        Some(name) => name,
        None => {
            println!("    -> Could not parse enclosing top-level definition name.");
            return None;
        }
    };
    let original_container = match extract_container_from_source(original_source, &container_name) {
        Some(container) => container,
        None => {
            println!(
                "    -> Could not extract original top-level definition {} from source.",
                container_name
            );
            return None;
        }
    };

    replace_top_level_definition_by_name(code, &container_name, &original_container)
}

fn replace_enclosing_container_span_from_source(
    code: &str,
    line_no: usize,
    original_source: &str,
) -> Option<String> {
    let lines: Vec<&str> = code.lines().collect();
    let container_start = match find_enclosing_container_start(&lines, line_no) {
        Some(start) => start,
        None => {
            println!("    -> Could not find enclosing top-level definition.");
            return None;
        }
    };
    let container_name = match parse_container_name(lines.get(container_start)?.trim_start()) {
        Some(name) => name,
        None => {
            println!("    -> Could not parse enclosing top-level definition name.");
            return None;
        }
    };
    let container_end = match find_block_end(&lines, container_start) {
        Some(end) => end,
        None => {
            println!(
                "    -> Could not find end for top-level definition {}.",
                container_name
            );
            return None;
        }
    };
    let original_container = match extract_container_from_source(original_source, &container_name) {
        Some(container) => container,
        None => {
            println!(
                "    -> Could not extract original top-level definition {} from source.",
                container_name
            );
            return None;
        }
    };

    let mut repaired = Vec::new();
    for line in lines.iter().take(container_start) {
        repaired.push((*line).to_string());
    }
    repaired.push(original_container);
    for line in lines.iter().skip(container_end + 1) {
        repaired.push((*line).to_string());
    }

    Some(repaired.join("\n"))
}

fn is_missing_symbol_error(err: &CompilerError) -> bool {
    let message = err.message.to_lowercase();
    err.category == CompilerErrorCategory::MissingSymbol
        || message.contains("undeclared identifier")
        || message.contains("identifier not found")
}

fn is_identifier_not_library_name_error(err: &CompilerError) -> bool {
    if err.code.as_deref() == Some("9589") {
        return true;
    }
    err.message
        .to_lowercase()
        .contains("identifier is not a library name")
}

fn find_enclosing_container_start(lines: &[&str], line_no: usize) -> Option<usize> {
    let start = line_no.saturating_sub(1).min(lines.len().saturating_sub(1));
    for idx in (0..=start).rev() {
        let trimmed = lines[idx].trim_start();
        if parse_container_name(trimmed).is_some() {
            return Some(idx);
        }
    }
    None
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
    if name.is_empty() {
        None
    } else {
        Some(name.to_string())
    }
}

fn find_block_end(lines: &[&str], start: usize) -> Option<usize> {
    let mut tracker = DepthTracker::default();

    for (idx, line) in lines.iter().enumerate().skip(start) {
        if tracker.process_line_and_check_end(line) {
            return Some(idx);
        }
    }

    None
}

fn extract_container_from_source(source: &str, container_name: &str) -> Option<String> {
    let lines: Vec<&str> = source.lines().collect();
    for (idx, line) in lines.iter().enumerate() {
        let trimmed = line.trim_start();
        if parse_container_name(trimmed).as_deref() == Some(container_name) {
            let end = find_block_end(&lines, idx)?;
            return Some(lines[idx..=end].join("\n"));
        }
    }
    None
}

fn inject_into_container(code: &str, container_name: &str, member_code: &str) -> Option<String> {
    let lines: Vec<&str> = code.lines().collect();
    for (idx, line) in lines.iter().enumerate() {
        let trimmed = line.trim_start();
        if parse_container_name(trimmed).as_deref() == Some(container_name) {
            let end = find_block_end(&lines, idx)?;
            let mut repaired = Vec::new();
            for line in lines.iter().take(end) {
                if idx == end {
                    // Handled below
                } else {
                    repaired.push((*line).to_string());
                }
            }

            let end_line = lines[end];
            if let Some(brace_idx) = end_line.rfind('}') {
                let before_brace = &end_line[..brace_idx];
                let after_brace = &end_line[brace_idx..];
                if !before_brace.trim().is_empty() || idx == end {
                    repaired.push(before_brace.to_string());
                }
                repaired.push(member_code.to_string());
                repaired.push(after_brace.to_string());
            } else {
                repaired.push(member_code.to_string());
                repaired.push(end_line.to_string());
            }

            for line in lines.iter().skip(end + 1) {
                repaired.push((*line).to_string());
            }
            return Some(repaired.join("\n"));
        }
    }
    None
}

fn looks_like_parser_error(err: &CompilerError) -> bool {
    let message = err.message.to_lowercase();
    err.category == CompilerErrorCategory::Syntax
        || message.contains("expected")
        || message.contains("unexpected")
        || message.contains("primary expression")
}

fn replace_enclosing_function_from_source(
    code: &str,
    line_no: usize,
    original_source: &str,
) -> Option<String> {
    let lines: Vec<&str> = code.lines().collect();
    let function_start = match find_enclosing_function_start(&lines, line_no) {
        Some(idx) => idx,
        None => {
            println!("    -> Could not find enclosing function start.");
            return None;
        }
    };
    let function_name = match parse_function_name(lines.get(function_start)?.trim()) {
        Some(name) => name,
        None => {
            println!("    -> Could not parse enclosing function name.");
            return None;
        }
    };
    let function_end = match find_function_end(&lines, function_start) {
        Some(idx) => idx,
        None => {
            println!("    -> Could not find end for function {}.", function_name);
            return None;
        }
    };

    println!(
        "    -> Found enclosing function {} from line {} to {}",
        function_name,
        function_start + 1,
        function_end + 1
    );

    // If the error line is outside the function body (floating code), replacing the function won't fix it.
    if line_no.saturating_sub(1) > function_end {
        println!("    -> Error at line {} is outside the bounds of enclosing function {} (ends at {}). This is floating code.", line_no, function_name, function_end + 1);
        return None;
    }

    let current_container_name = find_enclosing_container_start(&lines, function_start + 1)
        .and_then(|idx| parse_container_name(lines.get(idx)?.trim_start()));
    let preferred_param_count = function_param_count_from_lines(&lines, function_start);
    let original_function = current_container_name
        .as_deref()
        .and_then(|container_name| {
            extract_function_from_source_in_container(
                original_source,
                container_name,
                &function_name,
                preferred_param_count,
            )
        })
        .or_else(|| extract_function_from_source(original_source, &function_name));

    let original_function = match original_function {
        Some(function) => function,
        None => {
            println!(
                "    -> Could not extract original function {} from source.",
                function_name
            );
            return None;
        }
    };

    let mut repaired = Vec::new();
    for line in lines.iter().take(function_start) {
        repaired.push((*line).to_string());
    }
    repaired.push(original_function);
    for line in lines.iter().skip(function_end + 1) {
        repaired.push((*line).to_string());
    }

    Some(repaired.join("\n"))
}

fn extract_function_from_source_in_container(
    source: &str,
    container_name: &str,
    function_name: &str,
    preferred_param_count: Option<usize>,
) -> Option<String> {
    let lines: Vec<&str> = source.lines().collect();
    for (container_start, line) in lines.iter().enumerate() {
        if parse_container_name(line.trim_start()).as_deref() != Some(container_name) {
            continue;
        }

        let container_end = find_block_end(&lines, container_start)?;
        let mut tracker = DepthTracker::default();
        let mut fallback = None;

        for idx in container_start..=container_end {
            let trimmed = lines[idx].trim_start();
            if tracker.depth == 1
                && trimmed.starts_with("function ")
                && parse_function_name(trimmed).as_deref() == Some(function_name)
            {
                let function_end = find_function_end(&lines, idx)?;
                let function = lines[idx..=function_end].join("\n");
                let param_count = function_param_count_from_lines(&lines, idx);

                if preferred_param_count.is_some() && param_count == preferred_param_count {
                    return Some(function);
                }

                fallback.get_or_insert(function);
            }

            tracker.process_line_and_check_end(lines[idx]);
        }

        return fallback;
    }

    None
}

fn find_enclosing_function_start(lines: &[&str], line_no: usize) -> Option<usize> {
    let start = line_no.saturating_sub(1).min(lines.len().saturating_sub(1));
    for idx in (0..=start).rev() {
        let trimmed = lines[idx].trim_start();
        if trimmed.starts_with("function ") {
            return Some(idx);
        }
        if idx != start
            && (trimmed.starts_with("contract ")
                || trimmed.starts_with("library ")
                || trimmed.starts_with("interface "))
        {
            break;
        }
    }
    None
}

fn find_function_end(lines: &[&str], start: usize) -> Option<usize> {
    let mut tracker = DepthTracker::default();

    for (idx, line) in lines.iter().enumerate().skip(start) {
        if tracker.process_line_and_check_end(line) {
            return Some(idx);
        }

        if !tracker.seen_body && line.trim_end().ends_with(';') {
            return Some(idx);
        }
    }

    None
}

fn extract_function_from_source(source: &str, function_name: &str) -> Option<String> {
    let lines: Vec<&str> = source.lines().collect();
    for (idx, line) in lines.iter().enumerate() {
        let trimmed = line.trim_start();
        if trimmed.starts_with("function ")
            && parse_function_name(trimmed).as_deref() == Some(function_name)
        {
            let end = find_function_end(&lines, idx)?;
            return Some(lines[idx..=end].join("\n"));
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

fn parse_function_name(line: &str) -> Option<String> {
    let rest = line.trim_start().strip_prefix("function ")?;
    let name = rest
        .split(|ch: char| ch == '(' || ch.is_whitespace())
        .next()
        .unwrap_or("");
    if name.is_empty() {
        None
    } else {
        Some(name.to_string())
    }
}

fn find_previous_residue_line(lines: &[&str], line_no: usize) -> Option<usize> {
    let start = line_no.saturating_sub(1);
    let lower_bound = line_no.saturating_sub(6);

    for idx in (lower_bound..start).rev() {
        let line = lines.get(idx)?;
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }
        if normalizer::is_removable_residue_line(trimmed) {
            return Some(idx + 1);
        }

        // Stop at real Solidity statements; the culprit is normally adjacent
        // section text immediately above the parser-reported line.
        if trimmed.ends_with(';') || trimmed.ends_with('{') || trimmed.ends_with('}') {
            break;
        }
    }

    None
}

#[derive(Default, Clone)]
struct DepthTracker {
    pub depth: i32,
    pub in_multi_line_comment: bool,
    pub seen_body: bool,
}

impl DepthTracker {
    fn process_line_and_check_end(&mut self, line: &str) -> bool {
        let mut in_single_quote = false;
        let mut in_double_quote = false;
        let mut chars = line.chars().peekable();

        while let Some(ch) = chars.next() {
            if self.in_multi_line_comment {
                if ch == '*' && chars.peek() == Some(&'/') {
                    chars.next();
                    self.in_multi_line_comment = false;
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
                '/' => {
                    if chars.peek() == Some(&'/') {
                        break;
                    } else if chars.peek() == Some(&'*') {
                        chars.next();
                        self.in_multi_line_comment = true;
                    }
                }
                '\'' => in_single_quote = true,
                '"' => in_double_quote = true,
                '{' => {
                    self.depth += 1;
                    self.seen_body = true;
                }
                '}' => {
                    self.depth -= 1;
                    if self.depth <= 0 {
                        self.depth = 0;
                        if self.seen_body {
                            return true;
                        }
                    }
                }
                _ => {}
            }
        }
        false
    }
}

// ===== P0: Loop Detection =====

fn compute_logical_error_fingerprint(errors: &[CompilerError], code: &str) -> String {
    let lines: Vec<&str> = code.lines().collect();
    let mut parts = errors
        .iter()
        .map(|err| {
            let line_idx = err
                .line
                .and_then(|line_no| lines.get(line_no.saturating_sub(1)));
            let normalized_line = line_idx
                .map(|line| normalize_error_snippet_for_fingerprint(line))
                .or_else(|| {
                    err.snippet
                        .iter()
                        .find(|line| line.contains('|'))
                        .map(|line| normalize_error_snippet_for_fingerprint(line))
                })
                .unwrap_or_default();
            let logical_scope = err
                .line
                .map(|line_no| logical_error_scope(&lines, line_no))
                .unwrap_or_else(|| "<unknown>".to_string());
            format!(
                "{:?}:{}:{}:{}",
                err.category,
                normalize_compiler_message(&err.message),
                logical_scope,
                normalized_line
            )
        })
        .collect::<Vec<_>>();
    parts.sort();
    parts.dedup();
    parts.join(";;")
}

fn logical_error_scope(lines: &[&str], line_no: usize) -> String {
    let function_name = find_enclosing_function_start(lines, line_no)
        .and_then(|idx| parse_function_name(lines.get(idx)?.trim_start()))
        .unwrap_or_else(|| "<no-function>".to_string());
    let container_name = find_enclosing_container_start(lines, line_no)
        .and_then(|idx| parse_container_name(lines.get(idx)?.trim_start()))
        .unwrap_or_else(|| "<no-container>".to_string());
    format!("{}::{}", container_name, function_name)
}

fn normalize_compiler_message(message: &str) -> String {
    message
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ")
        .replace("Did you mean", "Suggestion")
}

/// Compute a stable fingerprint for a set of compiler errors that is independent of line numbers.
/// This allows detection of repeated error patterns even when line numbers shift due to code changes.
#[cfg(test)]
fn compute_error_fingerprint(errors: &[CompilerError]) -> String {
    let mut parts: Vec<String> = errors
        .iter()
        .map(|err| {
            // Use category + message + snippet content (but NOT line/column numbers)
            // to create a line-number-independent fingerprint
            let snippet_hash = if !err.snippet.is_empty() {
                err.snippet
                    .iter()
                    .map(|line| normalize_error_snippet_for_fingerprint(line))
                    .collect::<Vec<_>>()
                    .join("|")
            } else {
                String::new()
            };
            format!("{:?}:{}:{}", err.category, err.message, snippet_hash)
        })
        .collect();
    parts.sort();
    parts.dedup();
    parts.join(";;")
}

fn normalize_error_snippet_for_fingerprint(line: &str) -> String {
    let trimmed = line.trim();
    if let Some((maybe_line_no, rest)) = trimmed.split_once('|') {
        if maybe_line_no.trim().chars().all(|ch| ch.is_ascii_digit()) {
            return rest.trim().to_string();
        }
    }
    trimmed.to_string()
}

// ===== P0: Error Deduplication =====

/// Deduplicate compiler errors by their message content (ignoring line numbers).
/// Keeps the first occurrence of each unique error message.
fn deduplicate_errors(errors: Vec<CompilerError>) -> Vec<CompilerError> {
    let mut positions: HashMap<String, usize> = HashMap::new();
    let mut deduped: Vec<CompilerError> = Vec::new();

    for err in errors {
        let key = format!("{:?}:{}", err.category, err.message);
        if let Some(existing_idx) = positions.get(&key).copied() {
            if (deduped[existing_idx].line.is_none() && err.line.is_some())
                || (deduped[existing_idx].snippet.is_empty() && !err.snippet.is_empty())
            {
                deduped[existing_idx] = err;
            }
            continue;
        }

        positions.insert(key, deduped.len());
        deduped.push(err);
    }

    deduped
}

// ===== P0: Error Priority Sorting =====

fn sort_errors_by_priority(errors: &mut [CompilerError]) {
    errors.sort_by_key(|e| match e.category {
        CompilerErrorCategory::Syntax => 0,
        CompilerErrorCategory::MissingSymbol => 1,
        CompilerErrorCategory::Declaration => 2,
        CompilerErrorCategory::Duplicate => 3,
        CompilerErrorCategory::Type => 4,
        CompilerErrorCategory::Other => 5,
    });
}

// ===== P0: EVM Opcode Recognition =====

/// Returns true if the symbol is an EVM/Yul built-in opcode that should only be used
/// inside `assembly {}` blocks, not in regular Solidity code.
fn is_evm_opcode(symbol: &str) -> bool {
    matches!(
        symbol,
        // Arithmetic
        "add" | "sub" | "mul" | "div" | "sdiv" | "mod" | "smod" | "exp" |
        "addmod" | "mulmod" | "signextend" |
        // Comparison / Bitwise
        "lt" | "gt" | "slt" | "sgt" | "eq" | "iszero" |
        "and" | "or" | "xor" | "not" |
        "shl" | "shr" | "sar" | "byte" |
        // Keccak
        "keccak256" |
        // Environment
        "balance" | "origin" | "caller" | "callvalue" |
        "calldataload" | "calldatasize" | "calldatacopy" |
        "codesize" | "codecopy" | "gasprice" | "extcodesize" | "extcodecopy" |
        "returndatasize" | "returndatacopy" | "extcodehash" |
        // Block
        "blockhash" | "coinbase" | "prevrandao" |
        "gaslimit" | "chainid" | "selfbalance" | "basefee" |
        // Memory / Storage
        "mload" | "mstore" | "mstore8" | "sload" | "sstore" | "msize" |
        "tload" | "tstore" | "mcopy" |
        // Control flow (Yul)
        "pop" | "stop" | "invalid" |
        // Call
        "call" | "callcode" | "delegatecall" | "staticcall" |
        "create" | "create2" |
        // Log
        "log0" | "log1" | "log2" | "log3" | "log4" |
        // Gas
        "gas"
    )
}

// ===== P0: Assembly Wrapping Repair =====

/// When Yul opcodes (sub, shl, calldatasize, etc.) are used outside assembly blocks,
/// find the enclosing function and wrap the problematic statements in `assembly { ... }`.
fn try_wrap_in_assembly(code: &str, error_line_no: usize) -> Option<String> {
    let lines: Vec<&str> = code.lines().collect();
    let error_idx = error_line_no.saturating_sub(1);
    let error_line = lines.get(error_idx)?.trim();

    // Only handle statements that look like they use opcodes
    if !line_uses_evm_opcodes_as_calls(error_line) {
        return None;
    }

    // Find the function containing this line
    let func_start = find_enclosing_function_start(&lines, error_line_no)?;
    let func_end = find_function_end(&lines, func_start)?;

    // Scan all lines in this function for Yul opcode usage outside assembly blocks
    let mut in_assembly = false;
    let mut assembly_depth = 0i32;
    let mut lines_to_wrap: Vec<usize> = Vec::new(); // 0-indexed

    for idx in func_start..=func_end {
        if idx >= lines.len() {
            break;
        }
        let trimmed = lines[idx].trim();

        if trimmed.starts_with("assembly") && trimmed.contains('{') {
            in_assembly = true;
            assembly_depth = 0;
        }

        if in_assembly {
            assembly_depth += trimmed.chars().filter(|&c| c == '{').count() as i32;
            assembly_depth -= trimmed.chars().filter(|&c| c == '}').count() as i32;
            if assembly_depth <= 0 {
                in_assembly = false;
            }
            continue;
        }

        // Check if this line contains EVM opcodes used as function calls
        if line_uses_evm_opcodes_as_calls(trimmed) {
            lines_to_wrap.push(idx);
        }
    }

    if lines_to_wrap.is_empty() {
        return None;
    }

    // Build the repaired code by wrapping identified lines in assembly blocks
    let mut result: Vec<String> = Vec::new();
    let mut wrapped_set: HashSet<usize> = HashSet::new();

    for idx in 0..lines.len() {
        if lines_to_wrap.contains(&idx) && !wrapped_set.contains(&idx) {
            // Collect consecutive lines that need wrapping
            let indent = lines[idx].len() - lines[idx].trim_start().len();
            let indent_str = &lines[idx][..indent];

            result.push(format!("{}assembly {{", indent_str));

            let mut j = idx;
            while j < lines.len() && lines_to_wrap.contains(&j) {
                let yul_line = convert_solidity_to_yul(lines[j].trim());
                result.push(format!("{}    {}", indent_str, yul_line));
                wrapped_set.insert(j);
                j += 1;
            }

            result.push(format!("{}}}", indent_str));
        } else if !wrapped_set.contains(&idx) {
            result.push(lines[idx].to_string());
        }
    }

    Some(result.join("\n"))
}

/// Check if a line contains EVM opcodes used as direct function calls
/// (i.e., not inside an assembly block).
fn line_uses_evm_opcodes_as_calls(line: &str) -> bool {
    // Match patterns like: sub(...), shl(...), calldatasize()
    let opcodes = [
        "sub(",
        "add(",
        "mul(",
        "div(",
        "shl(",
        "shr(",
        "sar(",
        "and(",
        "or(",
        "xor(",
        "not(",
        "byte(",
        "calldatasize(",
        "calldataload(",
        "calldatacopy(",
        "mload(",
        "mstore(",
        "sload(",
        "sstore(",
        "returndatasize(",
        "returndatacopy(",
        "extcodesize(",
        "extcodecopy(",
    ];
    for opcode in &opcodes {
        if let Some(pos) = line.find(opcode) {
            if pos > 0 {
                let prev_char = line.as_bytes()[pos - 1];
                // It's a method call like obj.sub(...), not a standalone opcode
                if prev_char == b'.' || prev_char.is_ascii_alphanumeric() || prev_char == b'_' {
                    continue;
                }
            }
            return true;
        }
    }
    false
}

/// Convert a Solidity-style assignment with Yul opcodes to Yul syntax.
/// e.g., `offset = sub(shl(5, calldatasize()), 0x14);` -> `offset := sub(shl(5, calldatasize()), 0x14)`
fn convert_solidity_to_yul(line: &str) -> String {
    let mut yul_line = line.to_string();

    // Replace Solidity `=` with Yul `:=` (but not `==`, `!=`, `<=`, `>=`)
    if yul_line.contains(" = ") && !yul_line.contains(" == ") {
        yul_line = yul_line.replacen(" = ", " := ", 1);
    }

    // Remove trailing semicolons (Yul doesn't use them for assignments)
    if yul_line.trim_end().ends_with(';') {
        let trimmed = yul_line.trim_end();
        yul_line = trimmed[..trimmed.len() - 1].to_string();
    }

    // Remove type declarations like `uint256 offset = ...` -> `let offset := ...`
    let trimmed = yul_line.trim_start();
    let sol_types = [
        "uint256 ", "uint128 ", "uint64 ", "uint32 ", "uint16 ", "uint8 ", "int256 ", "int128 ",
        "int64 ", "int32 ", "int16 ", "int8 ", "address ", "bool ", "bytes32 ", "bytes ",
    ];
    for ty in &sol_types {
        if trimmed.starts_with(ty) {
            let rest = &trimmed[ty.len()..];
            yul_line = format!("let {}", rest);
            break;
        }
    }

    yul_line
}

#[cfg(test)]
mod tests {
    use super::*;

    fn syntax_error(line_no: usize, message: &str) -> CompilerError {
        CompilerError {
            code: Some("6933".to_string()),
            message: message.to_string(),
            file: None,
            line: Some(line_no),
            column: Some(13),
            category: CompilerErrorCategory::Syntax,
            snippet: vec![format!("{} |             );", line_no)],
        }
    }

    #[test]
    fn replaces_function_from_same_named_container_when_names_collide() {
        let code = r#"
library StateLibrary {
    function getFeeGrowthInside(IPoolManager manager, PoolId poolId, int24 tickLower, int24 tickUpper)
        internal
        view
        returns (uint256 feeGrowthInside0X128, uint256 feeGrowthInside1X128)
    {
        return (1, 2);
    }
}

library V4StateReader {
    function getFeeGrowthInside(IPoolManager manager, PoolId poolId, int24 tickLower, int24 tickUpper)
        internal
        view
        returns (uint256 feeGrowthInside0X128, uint256 feeGrowthInside1X128)
    {
        (uint256 feeGrowthGlobal0X128, uint256 feeGrowthGlobal1X128) = getFeeGrowthGlobals(manager, poolId);
        (, int24 tickCurrent,,) = getSlot0(manager, poolId);
    }
}
"#;

        let original_source = r#"
library StateLibrary {
    function getFeeGrowthInside(IPoolManager manager, PoolId poolId, int24 tickLower, int24 tickUpper)
        internal
        view
        returns (uint256 feeGrowthInside0X128, uint256 feeGrowthInside1X128)
    {
        return (3, 4);
    }
}

library V4StateReader {
    function getFeeGrowthInside(
        IPoolManager manager,
        PoolId idV4,
        int24 currentTick,
        int24 tickLower,
        int24 tickUpper
    ) internal view returns (uint256 feeGrowthInside0X128, uint256 feeGrowthInside1X128) {
        (uint256 lowerOut0, uint256 lowerOut1) = StateLibrary.getTickFeeGrowthOutside(
            manager,
            idV4,
            tickLower
        );
        return (lowerOut0, lowerOut1);
    }
}
"#;

        let repaired = replace_enclosing_function_from_source(code, 17, original_source)
            .expect("expected same-container function replacement");

        assert!(repaired.contains("PoolId idV4"));
        assert!(repaired.contains("int24 currentTick"));
        assert!(repaired.contains("StateLibrary.getTickFeeGrowthOutside"));
        assert!(!repaired.contains("return (3, 4);"));
    }

    #[test]
    fn counts_multiline_function_parameters() {
        let lines = [
            "    function getFeeGrowthInside(",
            "        IPoolManager manager,",
            "        PoolId idV4,",
            "        int24 currentTick,",
            "        int24 tickLower,",
            "        int24 tickUpper",
            "    ) internal view returns (uint256, uint256) {",
        ];

        assert_eq!(function_param_count_from_lines(&lines, 0), Some(5));
    }

    #[test]
    fn removes_trailing_comma_before_multiline_call_close() {
        let code = r#"
contract C {
    function f() external {
        assertEq(
            baselineNAV - navWithShort,
            shortPositionAmount,
        );
    }
}
"#;
        let line_no = code
            .lines()
            .position(|line| line.trim() == ");")
            .map(|idx| idx + 1)
            .expect("close line");
        let errors = vec![CompilerError {
            code: Some("6933".to_string()),
            message: "Expected primary expression.".to_string(),
            file: None,
            line: Some(line_no),
            column: Some(9),
            category: CompilerErrorCategory::Syntax,
            snippet: vec!["1 |         );".to_string()],
        }];

        let repaired = try_remove_trailing_comma_before_call_close(code, &errors)
            .expect("expected trailing comma repair");

        assert!(repaired.contains("            shortPositionAmount\n        );"));
        assert!(!repaired.contains("            shortPositionAmount,\n        );"));
    }

    #[test]
    fn removes_all_trailing_commas_before_multiline_call_closes() {
        let code = r#"
contract PoC {
    function test_submissionValidity() external {
        assertGt(
            availableForWithdrawal,
            0,
        );
        assertEq(
            availableForWithdrawal,
            2 * longPositionAmount,
        );
    }
}
"#;
        let line_no = code
            .lines()
            .position(|line| line.trim() == ");")
            .map(|idx| idx + 1)
            .expect("close line");
        let errors = vec![CompilerError {
            code: Some("6933".to_string()),
            message: "Expected primary expression.".to_string(),
            file: None,
            line: Some(line_no),
            column: Some(9),
            category: CompilerErrorCategory::Syntax,
            snippet: vec!["1 |         );".to_string()],
        }];

        let repaired = try_remove_trailing_comma_before_call_close(code, &errors)
            .expect("expected trailing comma repair");

        assert!(repaired.contains("            0\n        );"));
        assert!(repaired.contains("            2 * longPositionAmount\n        );"));
        assert!(!repaired.contains("            0,\n        );"));
        assert!(!repaired.contains("            2 * longPositionAmount,\n        );"));
    }

    #[test]
    fn trailing_comma_repair_stays_in_error_scope() {
        let code = r#"
library LiquidityChunkLibrary {
    function updateTickLower() internal pure {
        unchecked {
                );
        }
    }
}

contract PoC {
    function test_submissionValidity() external {
        assertGt(
            availableForWithdrawal,
            0,
        );
    }
}
"#;
        let line_no = code
            .lines()
            .position(|line| line.trim() == ");")
            .map(|idx| idx + 1)
            .expect("close line");
        let errors = vec![CompilerError {
            code: Some("6933".to_string()),
            message: "Expected primary expression.".to_string(),
            file: None,
            line: Some(line_no),
            column: Some(17),
            category: CompilerErrorCategory::Syntax,
            snippet: vec!["1 |                 );".to_string()],
        }];

        assert!(try_remove_trailing_comma_before_call_close(code, &errors).is_none());
    }

    #[test]
    fn removes_trailing_enum_comma_before_close() {
        let code = r#"
contract StdCheatsSafe {
    enum AddressType {
        Payable,
    }
}
"#;
        let errors = vec![CompilerError {
            code: Some("1612".to_string()),
            message: "Expected identifier after ','".to_string(),
            file: None,
            line: Some(5),
            column: Some(5),
            category: CompilerErrorCategory::Syntax,
            snippet: Vec::new(),
        }];

        let repaired = try_remove_trailing_enum_commas(code, &errors)
            .expect("expected enum trailing comma repair");

        assert!(repaired.contains("        Payable\n"));
        assert!(!repaired.contains("Payable,"));
    }

    #[test]
    fn removes_duplicate_vm_contract_when_interface_exists() {
        let code = r#"
contract Vm {
    function prank(address) external pure {}
}

interface Vm {
    function prank(address) external;
}

abstract contract Test {
    Vm public constant vm = Vm(address(0));
}
"#;
        let errors = vec![CompilerError {
            code: Some("2333".to_string()),
            message: "Identifier already declared.".to_string(),
            file: None,
            line: Some(2),
            column: Some(1),
            category: CompilerErrorCategory::Duplicate,
            snippet: Vec::new(),
        }];

        let repaired = try_remove_duplicate_top_level_definitions(code, &errors)
            .expect("expected duplicate Vm repair");

        assert!(!repaired.contains("contract Vm"));
        assert!(repaired.contains("interface Vm"));
        assert!(repaired.contains("abstract contract Test"));
    }

    #[test]
    fn restores_missing_multiline_expression_prefix_from_source() {
        let source = r#"
contract C {
    function f(uint256 amount, uint256 limit, bool ready) external pure returns (bool) {
        bool ok = ready
            && amount > 0
            && amount < limit;
        return ok;
    }
}
"#;
        let broken = r#"
contract C {
    function f(uint256 amount, uint256 limit, bool ready) external pure returns (bool) {
            && amount > 0
            && amount < limit;
        return ok;
    }
}
"#;

        let repaired = repair_orphan_multiline_expression_prefixes(broken, source, "test");

        assert!(repaired.contains("        bool ok = ready\n            && amount > 0"));
    }

    #[test]
    fn syntax_guided_restore_skips_target_test_function() {
        let source = r#"
contract PoC {
    function test_submissionValidity() external {
        uint256[] memory values = new uint256[](2);
        values[0] = uint256(keccak256("a"));
        values[1] = uint256(keccak256("b"));
    }
}
"#;
        let broken = r#"
contract PoC {
    function test_submissionValidity() external {
        uint256[] memory values = new uint256[](2);
            );
        values[1] = uint256(keccak256("b"));
    }
}
"#;
        let line_no = broken
            .lines()
            .position(|line| line.trim() == ");")
            .map(|idx| idx + 1)
            .expect("broken line");
        let errors = vec![syntax_error(line_no, "Expected primary expression.")];
        let source_index = SourceIndex::build(source);
        let target =
            HarnessValidationTarget::new("PoC".to_string(), "test_submissionValidity".to_string());

        let repair = try_syntax_error_guided_source_restore(
            broken,
            &errors,
            &source_index,
            &[],
            &[],
            &RestoreHistory::default(),
            broken.lines().count(),
            Some(&target),
        );

        assert!(repair.is_none());
    }

    #[test]
    fn syntax_guided_restore_does_not_repeat_restored_function() {
        let source = r#"
contract PoC {
    function helper() internal pure returns (uint256) {
        return uint256(keccak256("a"));
    }
}
"#;
        let broken = r#"
contract PoC {
    function helper() internal pure returns (uint256) {
            );
    }
}
"#;
        let line_no = broken
            .lines()
            .position(|line| line.trim() == ");")
            .map(|idx| idx + 1)
            .expect("broken line");
        let errors = vec![syntax_error(line_no, "Expected primary expression.")];
        let source_index = SourceIndex::build(source);
        let first = try_syntax_error_guided_source_restore(
            broken,
            &errors,
            &source_index,
            &[],
            &[],
            &RestoreHistory::default(),
            broken.lines().count(),
            None,
        )
        .expect("first restore");
        let mut history = RestoreHistory::default();
        history.record_success(&first);

        let second = try_syntax_error_guided_source_restore(
            broken,
            &errors,
            &source_index,
            &[],
            &[],
            &history,
            broken.lines().count(),
            None,
        );

        assert!(second.is_none());
    }

    #[test]
    fn detects_syntax_error_remaining_inside_restored_span() {
        let code = r#"
contract PoC {
    function helper() internal pure returns (uint256) {
            );
    }
}
"#;
        let line_no = code
            .lines()
            .position(|line| line.trim() == ");")
            .map(|idx| idx + 1)
            .expect("broken line");
        let source_index = SourceIndex::build(
            r#"
contract PoC {
    function helper() internal pure returns (uint256) {
        return 1;
    }
}
"#,
        );
        let source_function = source_index
            .function(Some("PoC"), "helper", Some(0))
            .expect("source function");
        let replacement = SourceReplacement {
            container_name: Some("PoC".to_string()),
            function_name: "helper".to_string(),
            param_count: Some(0),
            expected_hash: source_function.body_hash,
        };
        let errors = vec![syntax_error(line_no, "Expected primary expression.")];

        assert!(syntax_errors_in_restored_spans(
            code,
            &errors,
            &[],
            &[replacement],
            &[],
        ));
    }

    #[test]
    fn target_statement_restore_repairs_dangling_assert_without_full_function() {
        let source = r#"
contract PoC {
    function test_submissionValidity() external {
        uint256 baselineNAV = 1000 ether;
        uint256 navWithShort = 500 ether;
        uint256 shortPositionAmount = 500 ether;
        assertEq(
            baselineNAV - navWithShort,
            shortPositionAmount,
            "NAV should be reduced by short position amount"
        );
        uint256 longPositionAmount = 400 ether;
    }
}
"#;
        let broken = r#"
contract PoC {
    function test_submissionValidity() external {
        uint256 baselineNAV = 1000 ether;
        uint256 navWithShort = 500 ether;
        uint256 shortPositionAmount = 500 ether;
        assertEq(
            baselineNAV - navWithShort,
            shortPositionAmount,
        );
        uint256 longPositionAmount = 400 ether;
    }
}
"#;
        let line_no = broken
            .lines()
            .position(|line| line.trim() == ");")
            .map(|idx| idx + 1)
            .expect("broken line");
        let errors = vec![syntax_error(line_no, "Expected primary expression.")];
        let source_index = SourceIndex::build(source);
        let target =
            HarnessValidationTarget::new("PoC".to_string(), "test_submissionValidity".to_string());

        let repair = try_target_statement_restore(
            broken,
            &errors,
            &source_index,
            &[],
            &RestoreHistory::default(),
            broken.lines().count(),
            Some(&target),
        )
        .expect("target statement restore");

        assert_eq!(repair.statement_replacements.len(), 1);
        assert!(repair.source_replacements.is_empty());
        assert!(repair.container_replacements.is_empty());
        assert!(repair
            .code
            .contains("\"NAV should be reduced by short position amount\""));
        assert!(repair
            .code
            .contains("uint256 longPositionAmount = 400 ether;"));
    }

    #[test]
    fn syntax_guided_container_restore_respects_line_budget_and_falls_back_to_functions() {
        let source = r#"
contract PoC {
    function a() internal pure returns (uint256) {
        uint256 x = 1;
        uint256 y = 2;
        uint256 z = 3;
        return x + y + z;
    }

    function b() internal pure returns (uint256) {
        uint256 x = 1;
        uint256 y = 2;
        uint256 z = 3;
        return x + y + z;
    }
}
"#;
        let broken = r#"
contract PoC {
    function a() internal pure returns (uint256) {
            );
            );
    }
    function b() internal pure returns (uint256) {
            );
            );
    }
}
"#;
        let errors = broken
            .lines()
            .enumerate()
            .filter_map(|(idx, line)| {
                (line.trim() == ");").then(|| syntax_error(idx + 1, "Expected primary expression."))
            })
            .collect::<Vec<_>>();
        let source_index = SourceIndex::build(source);

        let repair = try_syntax_error_guided_source_restore(
            broken,
            &errors,
            &source_index,
            &[],
            &[],
            &RestoreHistory::default(),
            5,
            None,
        )
        .expect("function-level fallback restore");

        assert!(repair.container_replacements.is_empty());
        assert_eq!(repair.source_replacements.len(), 2);
    }

    #[test]
    fn source_container_repair_survives_post_processing_for_panoptic_math_ternary() {
        let source = r#"
library Strings_1 {
    function toString(uint256 value) internal pure returns (string memory) {
        value;
        return "";
    }
}

library PanopticMath {
    function uniswapFeeToString(uint24 fee) internal pure returns (string memory) {
        return
            fee == 0x800000
                ? "DYNAMIC"
                : string.concat(
                    Strings_1.toString(fee / 100),
                    fee % 100 == 0
                        ? ""
                        : string.concat(
                            ".",
                            Strings_1.toString((fee / 10) % 10),
                            Strings_1.toString(fee % 10)
                        ),
                    "bps"
                );
    }
}
"#;
        let broken = r#"
library Strings_1 {
    function toString(uint256 value) internal pure returns (string memory) {
        value;
        return "";
    }
}

library PanopticMath {
    function uniswapFeeToString(uint24 fee) internal pure returns (string memory) {
        return
            fee == 0x800000
                ? "DYNAMIC"
                : string.concat(
                        ? ""
                        : string.concat(
                    "bps"
                );
    }
}
"#;
        let source_index = SourceIndex::build(source);
        let source_container = source_index
            .container("PanopticMath")
            .expect("source container");
        let replacement = ContainerReplacement {
            container_name: "PanopticMath".to_string(),
            expected_hash: source_container.body_hash,
        };

        let protected =
            protect_source_replacements(broken, &[], &[replacement.clone()], &source_index);
        let processed = normalizer::normalize_solidity_fragment(&protected);
        let processed = protect_source_replacements(&processed, &[], &[replacement], &source_index);

        assert!(processed.contains("fee % 100 == 0"));
        assert!(processed.contains("Strings_1.toString((fee / 10) % 10)"));
        assert!(!processed.contains("string.concat(\n                        ? \"\""));
    }

    #[test]
    fn persistent_container_protection_preserves_previous_source_restore() {
        let source = r#"
type LiquidityChunk is uint256;

library LiquidityChunkLibrary {
    uint256 internal constant CLEAR_TL_MASK =
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF;

    function updateTickLower(
        LiquidityChunk self,
        int24 _tickLower
    ) internal pure returns (LiquidityChunk) {
        unchecked {
            return
                LiquidityChunk.wrap(LiquidityChunk.unwrap(self) & CLEAR_TL_MASK).addTickLower(
                    _tickLower
                );
        }
    }
}

library Strings_1 {
    function toString(uint256 value) internal pure returns (string memory) {
        value;
        return "";
    }
}

library PanopticMath {
    function uniswapFeeToString(uint24 fee) internal pure returns (string memory) {
        return
            fee == 0x800000
                ? "DYNAMIC"
                : string.concat(
                    Strings_1.toString(fee / 100),
                    fee % 100 == 0
                        ? ""
                        : string.concat(
                            ".",
                            Strings_1.toString((fee / 10) % 10),
                            Strings_1.toString(fee % 10)
                        ),
                    "bps"
                );
    }
}
"#;
        let source_index = SourceIndex::build(source);
        let liquidity = source_index
            .container("LiquidityChunkLibrary")
            .expect("liquidity container");
        let panoptic = source_index
            .container("PanopticMath")
            .expect("panoptic container");
        let replacements = vec![
            ContainerReplacement {
                container_name: "LiquidityChunkLibrary".to_string(),
                expected_hash: liquidity.body_hash,
            },
            ContainerReplacement {
                container_name: "PanopticMath".to_string(),
                expected_hash: panoptic.body_hash,
            },
        ];

        let processed = normalizer::normalize_solidity_fragment(source);
        let processed = protect_source_replacements(&processed, &[], &replacements, &source_index);

        assert!(processed.contains("LiquidityChunk.unwrap(self) & CLEAR_TL_MASK"));
        assert!(processed.contains("fee % 100 == 0"));
        assert!(!processed.contains("unchecked {\n                );"));
    }

    #[test]
    fn logical_error_fingerprint_ignores_line_drift_in_same_scope() {
        let code_a = r#"
contract PoC {
    function _setupDefaultOracles() internal {
        for (uint i = 0; i < 20; i++) {
            );
        }
    }
}
"#;
        let code_b = r#"
contract PoC {
    uint256 inserted0;
    uint256 inserted1;
    function _setupDefaultOracles() internal {
        for (uint i = 0; i < 20; i++) {
            );
        }
    }
}
"#;
        let line_a = code_a
            .lines()
            .position(|line| line.trim() == ");")
            .map(|idx| idx + 1)
            .unwrap();
        let line_b = code_b
            .lines()
            .position(|line| line.trim() == ");")
            .map(|idx| idx + 1)
            .unwrap();
        let err_a = CompilerError {
            code: Some("6933".to_string()),
            message: "Expected primary expression.".to_string(),
            file: None,
            line: Some(line_a),
            column: Some(13),
            category: CompilerErrorCategory::Syntax,
            snippet: Vec::new(),
        };
        let err_b = CompilerError {
            line: Some(line_b),
            ..err_a.clone()
        };

        assert_eq!(
            compute_logical_error_fingerprint(&[err_a], code_a),
            compute_logical_error_fingerprint(&[err_b], code_b)
        );
    }

    #[test]
    fn restores_stubbed_base_that_defines_missing_helper() {
        let code = r#"
abstract contract Clone {
    modifier onlyOwner() virtual { _; }
}

contract Pool is Clone {
    function collateralToken0() public pure returns (address) {
        return _getArgAddress(0);
    }
}
"#;
        let source = r#"
contract Clone {
    function _getArgAddress(uint256 argOffset) internal pure returns (address arg) {
        uint256 offset = _getImmutableArgsOffset();
        assembly {
            arg := shr(0x60, calldataload(add(offset, argOffset)))
        }
    }

    function _getImmutableArgsOffset() internal pure returns (uint256 offset) {
        assembly {
            offset := sub(calldatasize(), 2)
        }
    }
}

contract Pool is Clone {
    function collateralToken0() public pure returns (address) {
        return _getArgAddress(0);
    }
}
"#;

        let repaired = restore_base_container_defining_missing_symbol(code, 8, Some(16), source)
            .expect("expected Clone provider restoration");

        assert!(repaired.code.contains("function _getArgAddress"));
    }

    #[test]
    fn restores_using_library_dependency_closure() {
        let code = r#"
struct StdStorage {
    uint256 slot;
}

abstract contract StdCheats {
    using stdStorage for StdStorage;
}
"#;
        let source = r#"
struct StdStorage {
    uint256 slot;
}

library stdStorage {
    function find(StdStorage storage self) internal returns (uint256) {
        return stdStorageSafe.find(self);
    }
}

library stdStorageSafe {
    function find(StdStorage storage self) internal returns (uint256) {
        return self.slot;
    }
}
"#;
        let source_index = SourceIndex::build(source);
        let err = CompilerError {
            code: Some("9589".to_string()),
            message: "Identifier is not a library name.".to_string(),
            file: None,
            line: Some(7),
            column: Some(11),
            category: CompilerErrorCategory::Other,
            snippet: vec!["7 |     using stdStorage for StdStorage;".to_string()],
        };

        let repaired = try_restore_using_libraries_from_errors(code, &[err], &source_index)
            .expect("expected using-library closure restoration");

        assert!(repaired.code.contains("library stdStorage"));
        assert!(repaired.code.contains("library stdStorageSafe"));
        assert!(repaired
            .container_replacements
            .iter()
            .any(|replacement| replacement.container_name == "stdStorage"));
        assert!(repaired
            .container_replacements
            .iter()
            .any(|replacement| replacement.container_name == "stdStorageSafe"));
    }

    #[test]
    fn restores_allowed_base_when_symbol_has_multiple_providers() {
        let code = r#"
abstract contract ERC20Minimal {
    modifier onlyOwner() virtual { _; }
}

contract HypoVault is ERC20Minimal {
    function requestWithdrawal() external {
        uint256 userBalance = balanceOf[msg.sender];
        emit Transfer(address(0), msg.sender, userBalance);
    }
}
"#;
        let source = r#"
contract ERC1155 {
    mapping(address account => mapping(uint256 id => uint256 balance)) public balanceOf;
}

abstract contract ERC20Minimal {
    event Transfer(address indexed from, address indexed to, uint256 amount);
    uint256 public totalSupply;
    mapping(address account => uint256 balance) public balanceOf;
}

contract HypoVault is ERC20Minimal {
    function requestWithdrawal() external {
        uint256 userBalance = balanceOf[msg.sender];
        emit Transfer(address(0), msg.sender, userBalance);
    }
}
"#;

        let repaired = restore_base_container_defining_missing_symbol(code, 8, Some(31), source)
            .expect("expected ERC20Minimal base restoration");

        assert!(repaired.code.contains("abstract contract ERC20Minimal"));
        assert!(repaired
            .code
            .contains("mapping(address account => uint256 balance) public balanceOf"));
        assert!(!repaired.code.contains("mapping(address account => mapping"));
    }

    #[test]
    fn restores_provider_container_for_missing_library_member() {
        let code = r#"
library Math_2 {}

library Strings_1 {
    function numberOfLeadingHexZeros(address addr) external pure returns (uint256) {
        return addr == address(0) ? 40 : 39 - Math_2.mostSignificantNibble(uint160(addr));
    }
}
"#;
        let source = r#"
library Math_2 {
    function mostSignificantNibble(uint160 x) internal pure returns (uint256 r) {
        if (x >= 0x10) r += 1;
    }
}
"#;
        let err = CompilerError {
            code: Some("9582".to_string()),
            message: "Member \"mostSignificantNibble\" not found or not visible after argument-dependent lookup in type(library Math_2).".to_string(),
            file: None,
            line: Some(6),
            column: Some(47),
            category: CompilerErrorCategory::MissingSymbol,
            snippet: Vec::new(),
        };

        let repaired = restore_container_for_missing_member(code, &err, source)
            .expect("expected Math_2 provider restoration");

        assert!(repaired.code.contains("function mostSignificantNibble"));
        assert!(!repaired.code.contains("library Math_2 {}"));
        assert!(repaired.code.contains("function mostSignificantNibble"));
    }

    #[test]
    fn restores_provider_container_for_missing_contract_member() {
        let code = r#"
contract CollateralTracker {}

contract PanopticPool {
    function haircutPremia(CollateralTracker collateral0) internal {
        collateral0.exercise(address(0), 0, 0, 0, 0);
    }
}
"#;
        let source = r#"
contract CollateralTracker {
    function exercise(address, uint256, uint256, uint256, int128) external returns (int128) {
        return 0;
    }
}
"#;
        let err = CompilerError {
            code: Some("9582".to_string()),
            message: "Member \"exercise\" not found or not visible after argument-dependent lookup in contract CollateralTracker.".to_string(),
            file: None,
            line: Some(6),
            column: Some(21),
            category: CompilerErrorCategory::MissingSymbol,
            snippet: Vec::new(),
        };

        let repaired = restore_container_for_missing_member(code, &err, source)
            .expect("expected CollateralTracker provider restoration");

        assert!(repaired.code.contains("function exercise"));
        assert!(!repaired.code.contains("contract CollateralTracker {}"));
        assert!(repaired.code.contains("function exercise"));
    }

    #[test]
    fn restores_interface_bases_instead_of_inserting_interface_modifier_override() {
        let code = r#"
abstract contract IProtocolFees {
    modifier onlyOwner() virtual { _; }
}

abstract contract IERC6909Claims {
    modifier onlyOwner() virtual { _; }
}

interface IPoolManager is IProtocolFees, IERC6909Claims {}
"#;
        let source = r#"
interface IProtocolFees {
    function protocolFeeController() external view returns (address);
}

interface IERC6909Claims {
    function setOperator(address operator, bool approved) external returns (bool);
}

interface IPoolManager is IProtocolFees, IERC6909Claims {}
"#;
        let source_index = SourceIndex::build(source);
        let err = CompilerError {
            code: Some("6480".to_string()),
            message: "Derived contract must override modifier \"onlyOwner\". Two or more base classes define modifier with same name.".to_string(),
            file: None,
            line: Some(10),
            column: Some(1),
            category: CompilerErrorCategory::Other,
            snippet: vec![
                "10 | interface IPoolManager is IProtocolFees, IERC6909Claims {}".to_string(),
                "2 |     modifier onlyOwner() virtual { _; }".to_string(),
            ],
        };

        let repaired = try_restore_interface_bases_from_source(code, &[err], &source_index)
            .expect("expected interface base restoration");

        assert!(repaired.code.contains("interface IProtocolFees"));
        assert!(repaired.code.contains("interface IERC6909Claims"));
        assert!(!repaired.code.contains("modifier onlyOwner() override"));
        assert_eq!(repaired.container_replacements.len(), 2);
        assert!(insert_duplicate_modifier_override(&repaired.code, 10, "onlyOwner").is_none());
    }

    #[test]
    fn restores_source_function_for_return_arity_mismatch() {
        let code = r#"
type PositionBalance is uint256;

library PositionBalanceLibrary {
    function unpackTickData(uint96 _tickData) internal pure returns (int24, int24, int24, int24) {
        PositionBalance self = PositionBalance.wrap(uint256(_tickData) << 160);
        return (
        );
    }
}
"#;
        let source = r#"
type PositionBalance is uint256;

library PositionBalanceLibrary {
    function unpackTickData(uint96 _tickData) internal pure returns (int24, int24, int24, int24) {
        PositionBalance self = PositionBalance.wrap(uint256(_tickData) << 160);
        return (
            int24(int256(PositionBalance.unwrap(self) >> 160)),
            int24(int256(PositionBalance.unwrap(self) >> 184)),
            int24(int256(PositionBalance.unwrap(self) >> 208)),
            int24(int256(PositionBalance.unwrap(self) >> 232))
        );
    }
}
"#;
        let source_index = SourceIndex::build(source);
        let err = CompilerError {
            code: Some("5132".to_string()),
            message:
                "Different number of arguments in return statement than in returns declaration."
                    .to_string(),
            file: None,
            line: Some(7),
            column: Some(9),
            category: CompilerErrorCategory::Declaration,
            snippet: Vec::new(),
        };

        let repaired = try_restore_declaration_function_from_source(code, &[err], &source_index)
            .expect("expected function restoration");

        assert!(repaired.code.contains(">> 232"));
        assert!(!repaired.code.contains("return (\n        );"));
        assert_eq!(
            repaired.source_replacements[0].function_name,
            "unpackTickData"
        );
    }

    #[test]
    fn restores_explicit_missing_member_provider_before_ambiguous_extensions() {
        let code = r#"
library Strings_0 {
    function toString(uint256 value) internal pure returns (string memory) {
        value;
        return "zero";
    }
}

library Strings_1 {}

contract FeeHelper {
    function label(uint256 fee) internal pure returns (string memory) {
        return Strings_1.toString(fee);
    }
}
"#;
        let source = r#"
library Strings_0 {
    function toString(uint256 value) internal pure returns (string memory) {
        value;
        return "zero";
    }
}

library Strings_1 {
    function toString(uint256 value) internal pure returns (string memory) {
        value;
        return "one";
    }
}
"#;
        let err = CompilerError {
            code: Some("9582".to_string()),
            message: "Member \"toString\" not found or not visible after argument-dependent lookup in type(library Strings_1).".to_string(),
            file: None,
            line: Some(12),
            column: Some(16),
            category: CompilerErrorCategory::MissingSymbol,
            snippet: Vec::new(),
        };

        let repaired = restore_container_for_missing_member(code, &err, source)
            .expect("expected explicit Strings_1 provider restoration");

        assert!(repaired.code.contains("library Strings_1"));
        assert!(repaired.code.contains("return \"one\";"));
        assert!(!repaired.code.contains("library Strings_1 {}"));
        assert!(repaired.code.contains("function toString"));
    }

    #[test]
    fn restores_extension_provider_for_missing_member() {
        let code = r#"
type TokenId is uint256;
using TokenIdLibrary for TokenId global;

library TokenIdLibrary {}

library PanopticMath {
    function updatePositionsHash(TokenId tokenId) internal pure returns (uint256) {
        return tokenId.countLegs();
    }
}
"#;
        let source = r#"
type TokenId is uint256;
using TokenIdLibrary for TokenId global;

library TokenIdLibrary {
    function countLegs(TokenId self) internal pure returns (uint256 numLegs) {
        self;
        return 1;
    }
}
"#;
        let source_index = SourceIndex::build(source);
        let err = CompilerError {
            code: Some("9582".to_string()),
            message:
                "Member \"countLegs\" not found or not visible after argument-dependent lookup in TokenId."
                    .to_string(),
            file: None,
            line: Some(8),
            column: Some(24),
            category: CompilerErrorCategory::MissingSymbol,
            snippet: Vec::new(),
        };

        let repaired = restore_extension_provider_for_missing_member(code, &err, &source_index)
            .expect("expected TokenIdLibrary provider restoration");

        assert!(repaired.code.contains("function countLegs"));
        assert!(repaired.code.contains("function countLegs"));
    }

    #[test]
    fn restores_missing_top_level_provider_before_use() {
        let code = r#"
library Strings_0 {
    function toString(uint256 value) internal pure returns (string memory) {
        uint256 length = Math_0.log10(value) + 1;
        length;
        return "";
    }
}
"#;
        let source = r#"
library Math_0 {
    function log10(uint256 value) internal pure returns (uint256) {
        value;
        return 0;
    }
}
"#;
        let source_index = SourceIndex::build(source);

        let repaired = restore_missing_top_level_provider(code, 4, Some(26), &source_index)
            .expect("expected Math_0 provider restoration");

        assert!(repaired.code.contains("library Math_0"));
        assert!(
            repaired.code.find("library Math_0").unwrap()
                < repaired.code.find("library Strings_0").unwrap()
        );
    }

    #[test]
    fn restores_current_harness_container_for_missing_member() {
        let code = r#"
abstract contract Test {}

contract PoC is Test {
    HypoVault public vault;
    function setUp() public {
        mockAccountant = new VaultAccountantMock();
    }
}
"#;
        let source = r#"
abstract contract Test {}

contract PoC is Test {
    VaultAccountantMock public mockAccountant;
    HypoVault public vault;
    address Alice = address(0x123456);

    function setUp() public {
        mockAccountant = new VaultAccountantMock();
    }
}
"#;

        let repaired = restore_current_container_defining_missing_symbol(code, 7, Some(9), source)
            .expect("expected PoC container restoration");

        assert!(repaired
            .code
            .contains("VaultAccountantMock public mockAccountant"));
    }

    #[test]
    fn restores_synthetic_test_support_for_assert_and_console() {
        let code = r#"
abstract contract Test {}

contract PoC is Test {
    function testIt() external {
        assertGt(2, 1, "ok");
    }
}
"#;

        let repaired =
            restore_synthetic_test_support(code, 6, Some(9)).expect("expected Test shim");
        assert!(repaired.contains("abstract contract Test"));
        assert!(repaired.contains("function assertGt"));

        let console_code = r#"
contract PoC {
    function testIt() external {
        console.log("value", 1);
    }
}
"#;
        let repaired_console = restore_synthetic_test_support(console_code, 4, Some(9))
            .expect("expected console shim");
        assert!(repaired_console.contains("library console"));
    }

    #[test]
    fn error_fingerprint_ignores_snippet_line_number_drift() {
        let err_a = CompilerError {
            code: Some("2314".to_string()),
            message: "Expected ';' but got ','".to_string(),
            file: None,
            line: Some(6342),
            column: Some(51),
            category: CompilerErrorCategory::Syntax,
            snippet: vec!["6342 |                         managerPrices[i].poolPrice,".to_string()],
        };
        let err_b = CompilerError {
            line: Some(6437),
            snippet: vec!["6437 |                         managerPrices[i].poolPrice,".to_string()],
            ..err_a.clone()
        };

        assert_eq!(
            compute_error_fingerprint(&[err_a]),
            compute_error_fingerprint(&[err_b])
        );
    }
}
