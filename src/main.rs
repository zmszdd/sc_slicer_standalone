//!
//! SC Slicer - Solidity 代码切片工具（唯一 CLI 入口）
//!
//! 当前唯一切片引擎为 `sol_resurrect_v2`：以源码 span 文本索引为提取边界，
//! 从目标测试函数与关注符号出发做 source-backed 切片，并用 forge 编译保证单调回退。
//!
//! 旧的 analyzer/semantic_slicer/noise_reduction/source_normalizer 双实现已删除，
//! CLI 只负责解析参数、收集输入、调用 v2 并落盘结果，不再承载切片逻辑。

use clap::{Arg, Command};
use std::ffi::OsStr;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};

mod execution_log;
pub mod sol_resurrect_v2;

#[derive(Debug, Clone)]
struct TargetSpec {
    contract: String,
    entry_function: String,
    focus_symbol: String,
}

#[derive(Debug, Clone)]
struct CliConfig {
    input_path: String,
    target: TargetSpec,
    output_file: Option<String>,
    compile_guarantee: bool,
}

fn build_cli() -> Command {
    Command::new("SC_Slicer")
        .version("0.2.0")
        .author("SC_Slicer Team")
        .about("Source-backed Solidity code slice resurrection tool")
        .arg(
            Arg::new("input")
                .help("Path to the Solidity contract file or directory containing .sol files")
                .required(true)
                .index(1),
        )
        .arg(
            Arg::new("contract_name")
                .help("Name of the contract to analyze")
                .required(true)
                .index(2),
        )
        .arg(
            Arg::new("variable_name")
                .help("Name of the variable to slice")
                .required(true)
                .index(3),
        )
        .arg(
            Arg::new("function_name")
                .help("Optional: target test/function entry (legacy positional form)")
                .index(4),
        )
        .arg(
            Arg::new("target_test")
                .help("Target PoC test entry to preserve and validate with forge --match-test")
                .long("target-test")
                .value_name("FUNCTION"),
        )
        .arg(
            Arg::new("slice_level")
                .help("Slice level: 'function' (default) or 'line'")
                .long("level")
                .short('l')
                .value_parser(["function", "line"])
                .default_value("function"),
        )
        .arg(
            Arg::new("output")
                .help("Output file path (suppresses console output)")
                .long("output")
                .short('o')
                .value_name("FILE"),
        )
        .arg(
            Arg::new("exclude_libs")
                .help("Exclude library functions and contracts from output")
                .long("exclude-libs")
                .action(clap::ArgAction::SetTrue),
        )
        .arg(
            Arg::new("include_types")
                .help("Include type definitions and structs in output")
                .long("include-types")
                .action(clap::ArgAction::SetTrue)
                .default_value("true"),
        )
        .arg(
            Arg::new("semantic")
                .help("Deprecated: resurrection v2 is the only engine; accepted for compatibility")
                .long("semantic")
                .action(clap::ArgAction::SetTrue),
        )
        .arg(
            Arg::new("api_key")
                .help("Ignored: remote model calls are disabled")
                .long("api-key")
                .value_name("KEY"),
        )
        .arg(
            Arg::new("model")
                .help("Ignored: remote model calls are disabled")
                .long("model")
                .value_name("MODEL")
                .default_value("deepseek-ai/DeepSeek-V3.2"),
        )
        .arg(
            Arg::new("two_phase")
                .help("Deprecated: resurrection v2 is the only engine; accepted for compatibility")
                .long("two-phase")
                .action(clap::ArgAction::SetTrue),
        )
        .arg(
            Arg::new("llm_threshold")
                .help("Compatibility option; deterministic scoring ignores remote model calls")
                .long("llm-threshold")
                .value_name("SCORE")
                .default_value("30"),
        )
        .arg(
            Arg::new("parallel")
                .help("Compatibility option; remote model calls are disabled")
                .long("parallel")
                .action(clap::ArgAction::SetTrue),
        )
        .arg(
            Arg::new("max_concurrent")
                .help("Compatibility option; remote model calls are disabled")
                .long("max-concurrent")
                .value_name("NUM")
                .default_value("4"),
        )
        .arg(
            Arg::new("cache_file")
                .help("Enable persistent caching to file")
                .long("cache")
                .value_name("FILE")
                .default_value(".slicer_cache.json"),
        )
        .arg(
            Arg::new("prefilter")
                .help("Enable aggressive pre-filtering based on variable names")
                .long("prefilter")
                .action(clap::ArgAction::SetTrue),
        )
        .arg(
            Arg::new("max_level")
                .help("Maximum call level for contract hierarchy (default: 3, 0=target only, 1=direct calls, 2=indirect calls, etc.)")
                .long("max-level")
                .value_name("LEVEL")
                .default_value("3"),
        )
        .arg(
            Arg::new("aggressive_noise_reduction")
                .help("Enable aggressive noise reduction (stdlib stubbing, comment cleanup, type tree-shaking)")
                .long("aggressive-cleanup")
                .action(clap::ArgAction::SetTrue),
        )
        .arg(
            Arg::new("llm_completion")
                .help("Ignored: LLM completion is disabled to keep slices deterministic")
                .long("llm-completion")
                .action(clap::ArgAction::SetTrue),
        )
        .arg(
            Arg::new("resurrect_v2")
                .help("Deprecated: resurrection v2 is always enabled")
                .long("resurrect-v2")
                .action(clap::ArgAction::SetTrue),
        )
        .arg(
            Arg::new("compile_guarantee")
                .help("Allow resurrection v2 to widen monotonically up to the full source unit")
                .long("compile-guarantee")
                .action(clap::ArgAction::SetTrue),
        )
}

fn parse_cli() -> CliConfig {
    let matches = build_cli().get_matches();

    let input_path = matches.get_one::<String>("input").unwrap().to_string();
    let contract_name = matches
        .get_one::<String>("contract_name")
        .unwrap()
        .to_string();
    let variable_name = matches
        .get_one::<String>("variable_name")
        .unwrap()
        .to_string();
    let function_name = matches
        .get_one::<String>("target_test")
        .or_else(|| matches.get_one::<String>("function_name"))
        .map(|s| s.to_string())
        .unwrap_or_default();
    let output_file = matches.get_one::<String>("output").cloned();
    let compile_guarantee = matches.get_flag("compile_guarantee");

    CliConfig {
        input_path,
        target: TargetSpec {
            contract: contract_name,
            entry_function: function_name,
            focus_symbol: variable_name,
        },
        output_file,
        compile_guarantee,
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let config = parse_cli();

    let execution_log_path = resolve_execution_log_path(
        &config.target.contract,
        &config.target.entry_function,
        &config.target.focus_symbol,
        config.output_file.as_deref(),
    );
    let execution_log_path =
        execution_log::init(execution_log_path, &std::env::args().collect::<Vec<_>>())?;
    println!("📝 Execution log: {}", execution_log_path.display());

    execution_log::phase_start("configuration");
    execution_log::log_line(format!(
        "config input={} contract={} function={} variable={} compile_guarantee={} output={}",
        config.input_path,
        config.target.contract,
        if config.target.entry_function.is_empty() {
            "<all>"
        } else {
            &config.target.entry_function
        },
        config.target.focus_symbol,
        config.compile_guarantee,
        config.output_file.as_deref().unwrap_or("<stdout>")
    ));
    execution_log::phase_end("configuration", "ok");

    let (file_paths, source_codes) = collect_inputs(&config.input_path)?;
    log_input_files(&file_paths, &source_codes);

    println!("🚀 Starting source-backed Resurrection V2 (sole stage-1 engine)...");
    execution_log::log_line("resurrection_v2 pipeline started");

    let output_path = config
        .output_file
        .clone()
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("results/ResurrectedV2.t.sol"));

    let request = sol_resurrect_v2::ResurrectionV2Request {
        input_files: file_paths.iter().map(PathBuf::from).collect(),
        project_root: infer_project_root(&config.input_path),
        seed_slice: String::new(),
        target_contract: config.target.contract.clone(),
        target_test: config.target.entry_function.clone(),
        focus_symbol: config.target.focus_symbol.clone(),
        output_path: output_path.clone(),
        compile_guarantee: config.compile_guarantee,
    };

    let result = match sol_resurrect_v2::run_resurrection_v2(request).await {
        Ok(result) => result,
        Err(error) => {
            eprintln!("❌ Resurrection V2 failed: {error:#}");
            execution_log::log_line(format!("resurrection_v2 failed: {error:#}"));
            return Err(format!("Resurrection V2 failed: {error:#}").into());
        }
    };

    execution_log::log_line(format!(
        "resurrection_v2 returned lines={} compile_success={} fallback_level={}",
        result.code.lines().count(),
        result.metadata.compile_success,
        result.metadata.fallback_level
    ));

    write_output(&config, &result.code)?;
    execution_log::log_line("execution completed");
    Ok(())
}

fn collect_inputs(input_path: &str) -> Result<(Vec<String>, Vec<String>), String> {
    let file_paths = collect_sol_files(input_path)?;
    if file_paths.is_empty() {
        return Err(format!("No .sol files found in {}", input_path));
    }

    let mut source_codes = Vec::with_capacity(file_paths.len());
    for file_path in &file_paths {
        let source_code = fs::read_to_string(file_path)
            .map_err(|e| format!("Failed to read file {}: {}", file_path, e))?;
        source_codes.push(source_code);
    }
    Ok((file_paths, source_codes))
}

fn write_output(config: &CliConfig, code: &str) -> Result<(), Box<dyn std::error::Error>> {
    if let Some(output_file) = &config.output_file {
        fs::write(output_file, code)?;
        let mut log_file = OpenOptions::new()
            .create(true)
            .append(true)
            .open("analysis.log")?;
        writeln!(log_file, "✅ Results written to {}", output_file)?;
    } else {
        println!("{}", code);
    }
    Ok(())
}

fn resolve_execution_log_path(
    contract_name: &str,
    function_name: &str,
    variable_name: &str,
    output_file: Option<&str>,
) -> PathBuf {
    if let Ok(path) = std::env::var("SC_SLICER_LOG_FILE") {
        if !path.trim().is_empty() {
            return PathBuf::from(path);
        }
    }

    if let Some(output_file) = output_file {
        let output_path = Path::new(output_file);
        if let Some(stem) = output_path.file_stem().and_then(|stem| stem.to_str()) {
            let log_file = format!("{}.log", sanitize_log_name(stem));
            if let Some(parent) = output_path.parent().and_then(|p| p.parent()) {
                if !parent.as_os_str().is_empty() {
                    return parent.join("logs").join(log_file);
                }
            }
            return PathBuf::from("logs").join(log_file);
        }
    }

    let run_id = execution_log::unix_timestamp();
    let function_part = if function_name.trim().is_empty() {
        "all"
    } else {
        function_name
    };
    let file_name = format!(
        "slice_{}_{}_{}_{}.log",
        sanitize_log_name(contract_name),
        sanitize_log_name(function_part),
        sanitize_log_name(variable_name),
        run_id
    );
    PathBuf::from("logs").join(file_name)
}

fn infer_project_root(input_path: &str) -> PathBuf {
    let path = Path::new(input_path);
    let start = if path.is_file() {
        path.parent().unwrap_or_else(|| Path::new("."))
    } else {
        path
    };
    for ancestor in start.ancestors() {
        if ancestor.join("foundry.toml").exists() {
            return ancestor.to_path_buf();
        }
    }
    start.to_path_buf()
}

fn sanitize_log_name(value: &str) -> String {
    let sanitized = value
        .chars()
        .map(|ch| {
            if ch.is_ascii_alphanumeric() || ch == '_' || ch == '-' {
                ch
            } else {
                '_'
            }
        })
        .collect::<String>();
    if sanitized.is_empty() {
        "unknown".to_string()
    } else {
        sanitized
    }
}

fn log_input_files(file_paths: &[String], source_codes: &[String]) {
    let total_lines: usize = source_codes.iter().map(|code| code.lines().count()).sum();
    let total_bytes: usize = source_codes.iter().map(|code| code.len()).sum();
    execution_log::detail(
        "input_files",
        format!(
            "count={} total_lines={} total_bytes={}",
            file_paths.len(),
            total_lines,
            total_bytes
        ),
    );

    execution_log::sample(
        "input_file_paths",
        file_paths.iter().map(|path| path.as_str()),
        30,
    );

    for (path, code) in file_paths.iter().zip(source_codes.iter()).take(20) {
        execution_log::detail(
            "input_file",
            format!(
                "path={} lines={} bytes={}",
                path,
                code.lines().count(),
                code.len()
            ),
        );
    }
}

fn collect_sol_files(input_path: &str) -> Result<Vec<String>, String> {
    let path = Path::new(input_path);
    let mut files = Vec::new();

    if path.is_file() {
        if path.extension().and_then(|s| s.to_str()) == Some("sol") {
            files.push(input_path.to_string());
        }
    } else if path.is_dir() {
        collect_sol_files_recursive(path, &mut files)?;
    } else {
        return Err(format!(
            "Path {} is neither a file nor a directory",
            input_path
        ));
    }

    Ok(files)
}

fn collect_sol_files_recursive(dir: &Path, files: &mut Vec<String>) -> Result<(), String> {
    for entry in fs::read_dir(dir).map_err(|e| format!("Failed to read directory: {}", e))? {
        let entry: std::fs::DirEntry = entry.map_err(|e| format!("Failed to read entry: {}", e))?;
        let path = entry.path();

        if path.is_file() {
            if path.extension().and_then(|s: &OsStr| s.to_str()) == Some("sol") {
                files.push(path.to_string_lossy().to_string());
            }
        } else if path.is_dir()
            && !path.ends_with("node_modules")
            && !path.ends_with(".git")
            && !path.ends_with("target")
        {
            collect_sol_files_recursive(&path, files)?;
        }
    }

    Ok(())
}
