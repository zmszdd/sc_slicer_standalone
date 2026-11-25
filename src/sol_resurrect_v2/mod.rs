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

#[cfg(test)]
mod core_tests;

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
use validator::{CompileResult, CompileStatus, CompileValidator};

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

struct MetadataInput<'a> {
    source_db: &'a SourceDatabase,
    graph: &'a SliceGraph,
    fallback: &'a FallbackController,
    budget: &'a EffectiveSliceBudget,
    iterations: usize,
    code: &'a str,
    last_command: Option<String>,
    last_error_kind: Option<String>,
    original_project_uncompilable: bool,
}

#[derive(Debug, Clone)]
pub struct ResurrectionV2Result {
    pub code: String,
    pub metadata: ResurrectionV2Metadata,
}

struct ResurrectionRunner<'a> {
    request: &'a ResurrectionV2Request,
    source_db: &'a SourceDatabase,
    graph: SliceGraph,
    closure: ClosureEngine<'a>,
    renderer: SourceBackedRenderer<'a>,
    validator: CompileValidator,
    feedback: FeedbackController<'a>,
    fallback: FallbackController,
    budget: EffectiveSliceBudget,
    last_command: Option<String>,
    last_error_kind: Option<String>,
    final_code: String,
    iterations: usize,
}

impl<'a> ResurrectionRunner<'a> {
    fn new(request: &'a ResurrectionV2Request, source_db: &'a SourceDatabase) -> Self {
        let mut graph = SliceGraph::seed(
            request.target_contract.clone(),
            request.target_test.clone(),
            request.focus_symbol.clone(),
        );
        let mut closure = ClosureEngine::new(source_db);
        closure.apply_initial_closure(&mut graph);

        Self {
            request,
            source_db,
            graph,
            closure,
            renderer: SourceBackedRenderer::new(source_db),
            validator: CompileValidator::new(
                request.output_path.clone(),
                request.project_root.clone(),
                request.target_contract.clone(),
                request.target_test.clone(),
            ),
            feedback: FeedbackController::new(source_db),
            fallback: FallbackController::new(request.compile_guarantee),
            budget: EffectiveSliceBudget::default(),
            last_command: None,
            last_error_kind: None,
            final_code: String::new(),
            iterations: 0,
        }
    }

    fn render_current(&mut self) -> Result<()> {
        let render_level = self.fallback.level();
        self.graph.set_fallback_level(render_level);
        self.final_code = self
            .renderer
            .render(&self.graph)
            .with_context(|| format!("resurrect_v2 render failed at {:?}", render_level))?;
        std::fs::write(&self.request.output_path, &self.final_code)
            .with_context(|| format!("failed to write {}", self.request.output_path.display()))?;
        crate::execution_log::detail(
            "resurrection_v2_render",
            format!(
                "iteration={} level={} lines={} atoms={}",
                self.iterations,
                render_level.as_usize(),
                self.final_code.lines().count(),
                self.graph.atom_count()
            ),
        );
        Ok(())
    }

    async fn compile_current(&self) -> CompileResult {
        self.validator
            .compile(&self.final_code, self.fallback.level())
            .await
    }

    async fn handle_success(&mut self) -> Result<Option<ResurrectionV2Result>> {
        let metadata = metadata_for(MetadataInput {
            source_db: self.source_db,
            graph: &self.graph,
            fallback: &self.fallback,
            budget: &self.budget,
            iterations: self.iterations,
            code: &self.final_code,
            last_command: self.last_command.clone(),
            last_error_kind: None,
            original_project_uncompilable: false,
        });
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
            if self.fallback.widen(&mut self.graph) {
                let level = self.fallback.level();
                self.closure.apply_fallback_level(&mut self.graph, level);
                return Ok(None);
            }
        }

        let summary = format!(
            "compile_success={} slice_effective={} level={} iterations={}",
            metadata.compile_success,
            metadata.slice_effective,
            metadata.fallback_level,
            self.iterations
        );
        Ok(Some(self.finish(metadata, summary)?))
    }

    async fn handle_failed(
        &mut self,
        compile: CompileResult,
    ) -> Result<Option<ResurrectionV2Result>> {
        let action = self
            .feedback
            .analyze(&compile.errors, self.fallback.level());
        let updated = self.closure.apply_feedback(&mut self.graph, &action);
        crate::execution_log::detail(
            "resurrection_v2_feedback",
            format!(
                "iteration={} level={} action={:?} updated={}",
                self.iterations,
                self.fallback.level().as_usize(),
                action,
                updated
            ),
        );

        if !updated && !self.fallback.widen(&mut self.graph) {
            let original_status = self.validator.check_original_project().await;
            let original_project_uncompilable =
                matches!(original_status.status, CompileStatus::Failed);
            let failure_kind = if original_project_uncompilable {
                "original_project_uncompilable".to_string()
            } else {
                self.last_error_kind
                    .clone()
                    .unwrap_or_else(|| "renderer_or_toolchain_mismatch".to_string())
            };
            let metadata = metadata_for(MetadataInput {
                source_db: self.source_db,
                graph: &self.graph,
                fallback: &self.fallback,
                budget: &self.budget,
                iterations: self.iterations,
                code: &self.final_code,
                last_command: original_status.command.or(self.last_command.clone()),
                last_error_kind: Some(failure_kind),
                original_project_uncompilable,
            });
            let summary = format!(
                "compile_success=false original_project_uncompilable={}",
                original_project_uncompilable
            );
            return Ok(Some(self.finish(metadata, summary)?));
        }

        if !updated {
            let level = self.fallback.level();
            self.closure.apply_fallback_level(&mut self.graph, level);
        }
        Ok(None)
    }

    fn finish(
        &mut self,
        metadata: ResurrectionV2Metadata,
        summary: String,
    ) -> Result<ResurrectionV2Result> {
        write_metadata(&self.request.output_path, &metadata)?;
        crate::execution_log::phase_end("resurrection_v2", summary);
        Ok(ResurrectionV2Result {
            code: self.final_code.clone(),
            metadata,
        })
    }

    fn iteration_limit_result(&mut self) -> Result<ResurrectionV2Result> {
        let metadata = metadata_for(MetadataInput {
            source_db: self.source_db,
            graph: &self.graph,
            fallback: &self.fallback,
            budget: &self.budget,
            iterations: self.iterations,
            code: &self.final_code,
            last_command: self.last_command.clone(),
            last_error_kind: Some("fallback_iteration_limit".to_string()),
            original_project_uncompilable: false,
        });
        self.finish(metadata, "iteration_limit".to_string())
    }

    async fn run(mut self) -> Result<ResurrectionV2Result> {
        loop {
            self.iterations += 1;
            self.render_current()?;
            let compile = self.compile_current().await;
            self.last_command = compile.command.clone();
            self.last_error_kind = compile.primary_error_kind();

            match compile.status {
                CompileStatus::Success => {
                    if let Some(result) = self.handle_success().await? {
                        return Ok(result);
                    }
                }
                CompileStatus::ForgeUnavailable => {
                    let metadata = metadata_for(MetadataInput {
                        source_db: self.source_db,
                        graph: &self.graph,
                        fallback: &self.fallback,
                        budget: &self.budget,
                        iterations: self.iterations,
                        code: &self.final_code,
                        last_command: self.last_command.clone(),
                        last_error_kind: Some("forge_unavailable".to_string()),
                        original_project_uncompilable: false,
                    });
                    return self.finish(metadata, "forge_unavailable".to_string());
                }
                CompileStatus::Failed => {
                    if let Some(result) = self.handle_failed(compile).await? {
                        return Ok(result);
                    }
                }
            }

            if self.iterations >= MAX_FEEDBACK_ITERATIONS {
                return self.iteration_limit_result();
            }
        }
    }
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

    let runner = ResurrectionRunner::new(&request, &source_db);
    runner.run().await
}

fn metadata_for(input: MetadataInput<'_>) -> ResurrectionV2Metadata {
    let MetadataInput {
        source_db,
        graph,
        fallback,
        budget,
        iterations,
        code,
        last_command,
        last_error_kind,
        original_project_uncompilable,
    } = input;
    let level = fallback.level();
    let input_lines = source_db.total_nonblank_lines().max(1);
    let output_lines = code.lines().filter(|line| !line.trim().is_empty()).count();
    let input_bytes = source_db.total_bytes().max(1);
    let output_bytes = code.len();
    let line_ratio = output_lines as f64 / input_lines as f64;
    let byte_ratio = output_bytes as f64 / input_bytes as f64;
    let compile_success = last_error_kind.is_none() && !original_project_uncompilable;
    let full_source_unit_used =
        level == FallbackLevel::FullSourceUnit || line_ratio >= 0.95 || byte_ratio >= 0.95;
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
        failure_reason = if line_ratio > budget.max_line_ratio || byte_ratio > budget.max_byte_ratio
        {
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
