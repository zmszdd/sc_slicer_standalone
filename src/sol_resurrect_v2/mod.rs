#![allow(unused)]

pub mod closure;
pub mod diagnostics;
pub mod fallback;
pub mod feedback;
pub mod frontend;
pub mod renderer;
pub mod slice_atom;
pub mod slice_graph;
pub mod source_db;
pub mod source_index;
pub mod validator;

use std::path::PathBuf;

use anyhow::{Context, Result};
use serde::Serialize;

use closure::ClosureEngine;
use fallback::{FallbackController, FallbackLevel};
use feedback::FeedbackController;
use frontend::SourceFrontend;
use renderer::SourceBackedRenderer;
use slice_atom::SliceAtom;
use slice_graph::SliceGraph;
use source_db::SourceDatabase;
use validator::{CompileStatus, CompileValidator};

const MAX_FEEDBACK_ITERATIONS: usize = 192;

#[derive(Debug, Clone)]
pub struct ResurrectionV2Request {
    pub input_files: Vec<PathBuf>,
    pub project_root: PathBuf,
    pub seed_slice: String,
    pub target_contract: String,
    pub target_test: String,
    pub focus_symbol: String,
    pub output_path: PathBuf,
    pub compile_guarantee: bool,
}

#[derive(Debug, Clone, Serialize)]
pub struct ResurrectionV2Metadata {
    pub compile_success: bool,
    pub slice_effective: bool,
    pub input_lines: usize,
    pub fallback_level: usize,
    pub fallback_level_name: String,
    pub minimality: String,
    pub target_function_full_restored: bool,
    pub target_contract_full_restored: bool,
    pub container_fallback_used: bool,
    pub full_source_unit_used: bool,
    pub original_project_uncompilable: bool,
    pub llm_used: bool,
    pub iterations: usize,
    pub output_lines: usize,
    pub line_ratio: f64,
    pub input_bytes: usize,
    pub output_bytes: usize,
    pub byte_ratio: f64,
    pub max_line_ratio: f64,
    pub max_byte_ratio: f64,
    pub failure_reason: Option<String>,
    pub last_command: Option<String>,
    pub last_error_kind: Option<String>,
}

#[derive(Debug, Clone, Copy)]
struct EffectiveSliceBudget {
    max_line_ratio: f64,
    max_byte_ratio: f64,
}

impl Default for EffectiveSliceBudget {
    fn default() -> Self {
        Self {
            max_line_ratio: 0.25,
            max_byte_ratio: 0.30,
        }
    }
}

#[derive(Debug, Clone)]
pub struct ResurrectionV2Result {
    pub code: String,
    pub metadata: ResurrectionV2Metadata,
}

pub async fn run_resurrection_v2(request: ResurrectionV2Request) -> Result<ResurrectionV2Result> {
    crate::execution_log::phase_start("resurrection_v2");
    crate::execution_log::detail(
        "resurrection_v2_request",
        format!(
            "target={}.{} focus={} compile_guarantee={} files={} output={}",
            request.target_contract,
            request.target_test,
            request.focus_symbol,
            request.compile_guarantee,
            request.input_files.len(),
            request.output_path.display()
        ),
    );

    let source_db = SourceFrontend::parse_files(&request.input_files)
        .with_context(|| "resurrect_v2 failed to build SourceDatabase")?;
    source_db.log_summary();

    let mut graph = SliceGraph::seed(
        request.target_contract.clone(),
        request.target_test.clone(),
        request.focus_symbol.clone(),
    );
    let mut closure = ClosureEngine::new(&source_db);
    closure.apply_initial_closure(&mut graph);

    let renderer = SourceBackedRenderer::new(&source_db);
    let validator = CompileValidator::new(
        request.output_path.clone(),
        request.project_root.clone(),
        request.target_contract.clone(),
        request.target_test.clone(),
    );
    let feedback = FeedbackController::new(&source_db);
    let mut fallback = FallbackController::new(request.compile_guarantee);

    let mut last_command = None;
    let mut last_error_kind = None;
    let mut final_code = String::new();
    let mut iterations = 0usize;
    let budget = EffectiveSliceBudget::default();

    loop {
        iterations += 1;
        let render_level = fallback.level();
        graph.set_fallback_level(render_level);
        final_code = renderer
            .render(&graph)
            .with_context(|| format!("resurrect_v2 render failed at {:?}", render_level))?;
        std::fs::write(&request.output_path, &final_code)
            .with_context(|| format!("failed to write {}", request.output_path.display()))?;

        crate::execution_log::detail(
            "resurrection_v2_render",
            format!(
                "iteration={} level={} lines={} atoms={}",
                iterations,
                render_level.as_usize(),
                final_code.lines().count(),
                graph.atom_count()
            ),
        );

        let compile = validator.compile(&final_code, render_level).await;
        last_command = compile.command.clone();
        last_error_kind = compile.primary_error_kind();

        match compile.status {
            CompileStatus::Success => {
                let metadata = metadata_for(
                    &source_db,
                    &graph,
                    &fallback,
                    &budget,
                    iterations,
                    &final_code,
                    last_command,
                    None,
                    false,
                );
                if !metadata.slice_effective {
                    crate::execution_log::detail(
                        "resurrection_v2_effective_gate",
                        format!(
                            "compile_success=true slice_effective=false reason={} lines={}/{} ratio={:.3}",
                            metadata
                                .failure_reason
                                .clone()
                                .unwrap_or_else(|| "unknown".to_string()),
                            metadata.output_lines,
                            metadata.input_lines,
                            metadata.line_ratio
                        ),
                    );
                    if fallback.widen(&mut graph) {
                        let level = fallback.level();
                        closure.apply_fallback_level(&mut graph, level);
                        continue;
                    }
                }
                write_metadata(&request.output_path, &metadata)?;
                crate::execution_log::phase_end(
                    "resurrection_v2",
                    format!(
                        "compile_success={} slice_effective={} level={} iterations={}",
                        metadata.compile_success,
                        metadata.slice_effective,
                        metadata.fallback_level,
                        iterations
                    ),
                );
                return Ok(ResurrectionV2Result {
                    code: final_code,
                    metadata,
                });
            }
            CompileStatus::ForgeUnavailable => {
                let metadata = metadata_for(
                    &source_db,
                    &graph,
                    &fallback,
                    &budget,
                    iterations,
                    &final_code,
                    last_command,
                    Some("forge_unavailable".to_string()),
                    false,
                );
                write_metadata(&request.output_path, &metadata)?;
                crate::execution_log::phase_end("resurrection_v2", "forge_unavailable");
                return Ok(ResurrectionV2Result {
                    code: final_code,
                    metadata,
                });
            }
            CompileStatus::Failed => {
                let action = feedback.analyze(&compile.errors, fallback.level());
                let updated = closure.apply_feedback(&mut graph, &action);
                crate::execution_log::detail(
                    "resurrection_v2_feedback",
                    format!(
                        "iteration={} level={} action={:?} updated={}",
                        iterations,
                        fallback.level().as_usize(),
                        action,
                        updated
                    ),
                );

                if !updated && !fallback.widen(&mut graph) {
                    let original_status = validator.check_original_project().await;
                    let original_project_uncompilable =
                        matches!(original_status.status, CompileStatus::Failed);
                    let failure_kind = if original_project_uncompilable {
                        "original_project_uncompilable".to_string()
                    } else {
                        last_error_kind
                            .clone()
                            .unwrap_or_else(|| "renderer_or_toolchain_mismatch".to_string())
                    };
                    let metadata = metadata_for(
                        &source_db,
                        &graph,
                        &fallback,
                        &budget,
                        iterations,
                        &final_code,
                        original_status.command.or(last_command),
                        Some(failure_kind),
                        original_project_uncompilable,
                    );
                    write_metadata(&request.output_path, &metadata)?;
                    crate::execution_log::phase_end(
                        "resurrection_v2",
                        format!(
                            "compile_success=false original_project_uncompilable={}",
                            original_project_uncompilable
                        ),
                    );
                    return Ok(ResurrectionV2Result {
                        code: final_code,
                        metadata,
                    });
                }
                if !updated {
                    let level = fallback.level();
                    closure.apply_fallback_level(&mut graph, level);
                }
            }
        }

        if iterations >= MAX_FEEDBACK_ITERATIONS {
            let metadata = metadata_for(
                &source_db,
                &graph,
                &fallback,
                &budget,
                iterations,
                &final_code,
                last_command,
                Some("fallback_iteration_limit".to_string()),
                false,
            );
            write_metadata(&request.output_path, &metadata)?;
            crate::execution_log::phase_end("resurrection_v2", "iteration_limit");
            return Ok(ResurrectionV2Result {
                code: final_code,
                metadata,
            });
        }
    }
}

fn metadata_for(
    source_db: &SourceDatabase,
    graph: &SliceGraph,
    fallback: &FallbackController,
    budget: &EffectiveSliceBudget,
    iterations: usize,
    code: &str,
    last_command: Option<String>,
    last_error_kind: Option<String>,
    original_project_uncompilable: bool,
) -> ResurrectionV2Metadata {
    let level = fallback.level();
    let input_lines = source_db.total_nonblank_lines().max(1);
    let output_lines = code.lines().filter(|line| !line.trim().is_empty()).count();
    let input_bytes = source_db.total_bytes().max(1);
    let output_bytes = code.len();
    let line_ratio = output_lines as f64 / input_lines as f64;
    let byte_ratio = output_bytes as f64 / input_bytes as f64;
    let compile_success = last_error_kind.is_none() && !original_project_uncompilable;
    let full_source_unit_used = level == FallbackLevel::FullSourceUnit || line_ratio >= 0.95 || byte_ratio >= 0.95;
    let target_contract_full_restored = graph.container_fallback_used();
    let target_function_full_restored = target_contract_full_restored
        || source_db
            .resolve_function(&graph.target_contract, &graph.target_function)
            .is_some_and(|target_fn| {
                graph
                    .atoms
                    .iter()
                    .any(|atom| matches!(atom, SliceAtom::Function(fid) if *fid == target_fn))
            });
    let mut failure_reason = last_error_kind.clone();
    if compile_success {
        failure_reason = if line_ratio > budget.max_line_ratio || byte_ratio > budget.max_byte_ratio {
            Some("compile_artifact_not_effective_slice".to_string())
        } else if full_source_unit_used {
            Some("full_source_unit_restored".to_string())
        } else if target_contract_full_restored {
            Some("target_contract_full_restored".to_string())
        } else if target_function_full_restored {
            Some("target_function_full_restored".to_string())
        } else {
            None
        };
    }
    let slice_effective = compile_success
        && failure_reason.is_none()
        && line_ratio <= budget.max_line_ratio
        && byte_ratio <= budget.max_byte_ratio
        && !full_source_unit_used
        && !target_contract_full_restored
        && !target_function_full_restored;
    ResurrectionV2Metadata {
        compile_success,
        slice_effective,
        input_lines,
        fallback_level: level.as_usize(),
        fallback_level_name: level.name().to_string(),
        minimality: level.minimality().to_string(),
        target_function_full_restored,
        target_contract_full_restored,
        container_fallback_used: graph.container_fallback_used(),
        full_source_unit_used,
        original_project_uncompilable,
        llm_used: false,
        iterations,
        output_lines,
        line_ratio,
        input_bytes,
        output_bytes,
        byte_ratio,
        max_line_ratio: budget.max_line_ratio,
        max_byte_ratio: budget.max_byte_ratio,
        failure_reason,
        last_command,
        last_error_kind,
    }
}

fn write_metadata(output_path: &std::path::Path, metadata: &ResurrectionV2Metadata) -> Result<()> {
    let mut metadata_path = output_path.to_path_buf();
    let file_name = output_path
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or("resurrect_v2.sol");
    metadata_path.set_file_name(format!("{}.v2.json", file_name));
    let json = serde_json::to_string_pretty(metadata)?;
    std::fs::write(&metadata_path, json)?;
    crate::execution_log::detail(
        "resurrection_v2_metadata",
        format!("path={}", metadata_path.display()),
    );
    Ok(())
}
