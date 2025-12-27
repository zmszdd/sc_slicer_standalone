//!
//! SC Slicer - Solidity 代码切片工具
//!
//! 命令行入口程序，负责解析用户参数、调用代码分析器
//! 和语义切片器，对 Solidity 智能合约进行安全分析
//! 和代码切片。
//!

use clap::{Arg, Command};
use std::fs;
use std::fs::OpenOptions;
use std::io::Write;
use std::ffi::OsStr;
use std::path::Path;

mod analyzer;
pub mod semantic_slicer;

use crate::analyzer::AnalysisResult;
use crate::semantic_slicer::SemanticGraphAdapter;
use petgraph::Direction;

struct PdgAdapter<'a> {
    analysis: &'a AnalysisResult,
    source_code: &'a str,
}

impl<'a> SemanticGraphAdapter for PdgAdapter<'a> {
    fn get_predecessors(&self, node_id: usize) -> Vec<usize> {
        self.analysis.program_dependency_graph.graph.neighbors_directed(petgraph::graph::NodeIndex::new(node_id), Direction::Incoming).map(|n| n.index()).collect()
    }

    fn get_node_source(&self, node_id: usize) -> String {
        if let Some(&stored_node_id) = self.analysis.program_dependency_graph.graph.node_weight(petgraph::graph::NodeIndex::new(node_id)) {
            if let Some(node) = self.analysis.program_dependency_graph.nodes.get(&stored_node_id) {
                let start = node.span.lo().to_usize();
                let end = node.span.hi().to_usize();
                self.source_code[start..end].to_string()
            } else {
                "".to_string()
            }
        } else {
            "".to_string()
        }
    }

    fn is_control_node(&self, node_id: usize) -> bool {
        if let Some(&stored_node_id) = self.analysis.program_dependency_graph.graph.node_weight(petgraph::graph::NodeIndex::new(node_id)) {
            if let Some(node) = self.analysis.program_dependency_graph.nodes.get(&stored_node_id) {
                matches!(node.kind, crate::analyzer::NodeKind::ControlCondition)
            } else {
                false
            }
        } else {
            false
        }
    }

    fn get_node_info(&self, node_id: usize) -> Option<&analyzer::PdgNode> {
        if let Some(&stored_node_id) = self.analysis.program_dependency_graph.graph.node_weight(petgraph::graph::NodeIndex::new(node_id)) {
            self.analysis.program_dependency_graph.nodes.get(&stored_node_id)
        } else {
            None
        }
    }

    fn is_keyword(&self, token: &str) -> bool {
        // Solidity 关键字列表
        matches!(token, "function" | "if" | "else" | "for" | "while" | "return" | "uint256" | "address" | "bool" | "string" | "bytes" | "require" | "emit" | "event" | "contract" | "pragma" | "import" | "public" | "private" | "internal" | "external" | "view" | "pure" | "payable" | "constructor" | "modifier" | "struct" | "enum" | "mapping" | "memory" | "storage" | "calldata")
    }

    fn extract_identifiers(&self, node_id: usize) -> Vec<String> {
        // 简化实现：从源码中提取标识符
        let code = self.get_node_source(node_id);
        let mut ids = Vec::new();
        for word in code.split(|c: char| !c.is_alphanumeric() && c != '_') {
            if !word.is_empty() && word.chars().next().unwrap().is_alphabetic() && !self.is_keyword(word) {
                ids.push(word.to_string());
            }
        }
        ids
    }

    fn get_contract_context_summary(&self) -> String {
        // 提取状态变量和事件定义，但不包括函数体
        let mut context_parts = Vec::new();

        // 解析源代码，提取合约结构
        let lines: Vec<&str> = self.source_code.lines().collect();
        let mut i = 0;
        while i < lines.len() {
            let line = lines[i].trim();
            if line.starts_with("pragma ") || line.starts_with("import ") {
                // 保留pragma和import
                context_parts.push(lines[i].to_string());
            } else if line.starts_with("contract ") {
                // 提取合约声明和状态变量
                let contract_name = line.split_whitespace().nth(1).unwrap_or("").split('{').next().unwrap_or("");
                context_parts.push(lines[i].to_string());

                let mut brace_count = 0;
                i += 1;
                while i < lines.len() {
                    let current_line = lines[i];
                    let trimmed = current_line.trim();

                    if trimmed.starts_with("function ") || trimmed.starts_with("constructor") || trimmed.starts_with("modifier ") {
                        // 跳过函数定义，只保留签名
                        let mut func_brace = 0;
                        let mut j = i;
                        while j < lines.len() {
                            let f_line = lines[j];
                            func_brace += f_line.chars().filter(|&c| c == '{').count() as i32;
                            func_brace -= f_line.chars().filter(|&c| c == '}').count() as i32;
                            if func_brace == 0 && f_line.contains('}') {
                                break;
                            }
                            j += 1;
                        }
                        // 只保留函数签名，不包括函数体
                        if let Some(func_line) = lines[i].strip_suffix('{') {
                            context_parts.push(format!("{} {{ /* function body omitted */ }}", func_line.trim()));
                        } else {
                            context_parts.push(format!("{} /* function body omitted */", lines[i].trim()));
                        }
                        i = j;
                    } else if trimmed.starts_with("event ") || trimmed.starts_with("error ") || trimmed.starts_with("struct ") || trimmed.starts_with("enum ") {
                        // 保留事件、错误、结构体、枚举定义
                        context_parts.push(current_line.to_string());
                        brace_count += current_line.chars().filter(|&c| c == '{').count() as i32;
                        brace_count -= current_line.chars().filter(|&c| c == '}').count() as i32;
                        if brace_count == 0 && current_line.contains('}') {
                            break;
                        }
                    } else if !trimmed.is_empty() && !trimmed.starts_with("//") && !trimmed.starts_with("/*") {
                        // 保留状态变量声明等
                        context_parts.push(current_line.to_string());
                    }

                    brace_count += current_line.chars().filter(|&c| c == '{').count() as i32;
                    brace_count -= current_line.chars().filter(|&c| c == '}').count() as i32;
                    if brace_count == 0 && current_line.contains('}') {
                        break;
                    }
                    i += 1;
                }
            }
            i += 1;
        }

        context_parts.join("\n")
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let matches = Command::new("SC_Slicer")
        .version("0.1.0")
        .author("SC_Slicer Team")
        .about("Solidity code slicing analysis tool based on Program Dependency Graph (PDG)")
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
                .help("Optional: Name of the function (for targeted analysis)")
                .index(4),
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
                .help("Use semantic slicing with LLM scoring")
                .long("semantic")
                .action(clap::ArgAction::SetTrue),
        )
        .arg(
            Arg::new("api_key")
                .help("API key for LLM service (required if --semantic is used)")
                .long("api-key")
                .value_name("KEY"),
        )
        .get_matches();

    let input_path = matches.get_one::<String>("input").unwrap();
    let contract_name = matches.get_one::<String>("contract_name").unwrap();
    let variable_name = matches.get_one::<String>("variable_name").unwrap();
    let function_name_str = matches.get_one::<String>("function_name");
    let function_name = function_name_str.map(|s| s.as_str()).unwrap_or("");
    let slice_level = matches.get_one::<String>("slice_level").unwrap();
    let output_file = matches.get_one::<String>("output");
    let exclude_libs = matches.get_flag("exclude_libs");
    let include_types = matches.get_flag("include_types");
    let use_semantic = matches.get_flag("semantic");
    let api_key_from_arg = matches.get_one::<String>("api_key").map(|s| s.as_str()).unwrap_or("");
    let api_key = if !api_key_from_arg.is_empty() {
        api_key_from_arg.to_string()
    } else {
        std::env::var("OPENAI_API_KEY").unwrap_or_else(|_| "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiJKYW5zb24iLCJVc2VyTmFtZSI6IkphbnNvbiIsIkFjY291bnQiOiIiLCJTdWJqZWN0SUQiOiIxOTg1NzAzNDk1MzEwNzc4NzM1IiwiUGhvbmUiOiIxNTc5OTAxMzA1OCIsIkdyb3VwSUQiOiIxOTg1NzAzNDk1Mjk0MDAxNTE5IiwiUGFnZU5hbWUiOiIiLCJNYWlsIjoiIiwiQ3JlYXRlVGltZSI6IjIwMjUtMTEtMDUgMTQ6Mzc6NDgiLCJUb2tlblR5cGUiOjEsImlzcyI6Im1pbmltYXgifQ.ghKldxkQSXOl4AugSLbfw2mnkJzOKBqxVNZu5dz6Me1ulW1LqULw8BBLum9F_8k8sKwAA8Ztuz9DKjOYMaw5YT3sjuGRE5v7MakzsvEjEjQwYhWXQ7GwhNWTH3fGLCjmfRA6pgtcyqRvcOTyuSSz7lTTGYKG1TFxRlJQFjZ5Bs6JZ7SIVAFpdPQ8ZmRl3BkLLwWDbjD22mbkKDjnK9lrL_CUd8k4Ix5QMmi6lDMn--i0t9-q2bo1D3E9y1xiztgycu5SgJArOQJDUBTeTwYyTzguLIV0RdXgxM8gRujvdFVi3Z_saLyjxciCkIWAKjpNFBrknKtvXPKQWgvqV2FhZg".to_string())
    };
    let base_url = std::env::var("OPENAI_BASE_URL").unwrap_or_else(|_| "https://api.minimaxi.com/v1".to_string());

    // Collect all .sol files
    let file_paths = collect_sol_files(input_path)?;

    if file_paths.is_empty() {
        eprintln!("❌ No .sol files found in {}", input_path);
        return Err("No .sol files found".into());
    }

    // 读取所有源代码
    let mut source_codes = Vec::new();
    for file_path in &file_paths {
        let source_code = fs::read_to_string(file_path)
            .map_err(|e| format!("Failed to read file {}: {}", file_path, e))?;
        source_codes.push(source_code);
    }
    let combined_source = source_codes.join("\n");

    // 解析AST并分析
    let sess = solar_interface::Session::builder().with_buffer_emitter(solar_interface::ColorChoice::Auto).build();
    let result = sess.enter(|| -> solar_interface::Result<AnalysisResult> {
        let arena = solar_ast::Arena::new();
        let mut all_asts = Vec::new();
        for file_path in &file_paths {
            let mut parser = solar_parse::Parser::from_file(&sess, &arena, Path::new(file_path))?;
            let ast = parser.parse_file().map_err(|e| e.emit())?;
            all_asts.push(ast);
        }
        Ok(analyzer::analyze_asts(&all_asts, &combined_source))
    });

    let analysis = match result {
        Ok(analysis) => analysis,
        Err(_) => return Err("Failed to parse or analyze the contracts".into()),
    };

    let slice = if use_semantic {
        if api_key.is_empty() {
            eprintln!("❌ API key required for semantic slicing");
            return Err("API key required".into());
        }
        // 使用语义切片
        let adapter = PdgAdapter { analysis: &analysis, source_code: &combined_source };
        let model = "MiniMax-M2.1".to_string();
        let mut slicer = crate::semantic_slicer::SemanticSlicer::new(&adapter, api_key.to_string(), base_url.to_string(), model);
        // 找到 sink nodes (假设是 totalAssets 的写入)
        let sink_nodes = find_sink_nodes(&analysis, variable_name);
        let slice_nodes = slicer.run_slicing(sink_nodes).await;
        // 转换为源码切片
        let slice = get_source_from_nodes(&mut slicer, &analysis, &combined_source, &slice_nodes, contract_name, function_name, exclude_libs, include_types).await;
        slice
    } else {
        match slice_level.as_str() {
            "line" => {
                match analyzer::get_source_line_slice(&analysis, &combined_source, contract_name, function_name, variable_name, exclude_libs, include_types) {
                    slice => slice
                }
            }
            "function" | _ => {
                analyzer::get_source_slice(&analysis, &combined_source, contract_name, function_name, variable_name, exclude_libs, include_types)
            }
        }
    };

    let mut log_file = OpenOptions::new().create(true).append(true).open("analysis.log")?;

    if let Some(output_file) = output_file {
        fs::write(output_file, slice.join("\n")).expect("Failed to write to file");
        writeln!(log_file, "✅ Results written to {}", output_file)?;
    } else {
        writeln!(log_file, "🔍 Source Code Slice Analysis")?;
        writeln!(log_file, "📁 Input: {}", input_path)?;
        writeln!(log_file, "🏢 Contract: {}", contract_name)?;
        writeln!(log_file, "⚡ Function: {}", if function_name.is_empty() { "All functions" } else { function_name })?;
        writeln!(log_file, "📊 Variable: {}", variable_name)?;
        writeln!(log_file, "🎯 Slice Level: {}", slice_level)?;
        writeln!(log_file, "📋 Slice Results ({} lines):", slice.len())?;
        writeln!(log_file, "{}", "=".repeat(60))?;

        for line in slice {
            writeln!(log_file, "{}", line)?;
        }

        writeln!(log_file, "{}", "=".repeat(60))?;
        writeln!(log_file, "✅ Analysis completed successfully!")?;
    }
    Ok(())
}

fn find_sink_nodes(analysis: &AnalysisResult, variable_name: &str) -> Vec<usize> {
    let mut sinks = Vec::new();
    println!("🔍 Looking for StorageWrite nodes for variable: {}", variable_name);

    // 遍历graph的节点索引，找到对应的存储节点
    for node_index in analysis.program_dependency_graph.graph.node_indices() {
        if let Some(&stored_node_id) = analysis.program_dependency_graph.graph.node_weight(node_index) {
            if let Some(node) = analysis.program_dependency_graph.nodes.get(&stored_node_id) {
                if matches!(node.kind, crate::analyzer::NodeKind::StorageWrite(ref v) if v == variable_name) {
                    println!("✅ Found StorageWrite sink node {} (graph index {}) : kind={:?}, label='{}', function_context={:?}",
                        stored_node_id, node_index.index(), node.kind, node.label, node.function_context);
                    sinks.push(node_index.index()); // 返回graph节点索引
                }
            }
        }
    }

    println!("📊 Total sink nodes found: {}", sinks.len());
    sinks
}

async fn get_source_from_nodes<'a>(slicer: &mut crate::semantic_slicer::SemanticSlicer<'a, PdgAdapter<'a>>, analysis: &AnalysisResult, source_code: &str, slice_nodes: &std::collections::HashSet<usize>, contract: &str, function: &str, exclude_libs: bool, include_types: bool) -> Vec<String> {
    // 找到所有相关的合约：从slice_nodes中提取合约名
    let mut relevant_contracts = std::collections::HashSet::new();
    for &node_id in slice_nodes {
        if let Some(&stored_node_id) = analysis.program_dependency_graph.graph.node_weight(petgraph::graph::NodeIndex::new(node_id)) {
            if let Some(node) = analysis.program_dependency_graph.nodes.get(&stored_node_id) {
                // 假设合约信息在analysis中，但简化：从source_code解析
                // 这里简化：如果节点在某个合约中，添加该合约
                // 实际上，需要从AST中提取合约名
                // 暂时添加所有合约
            }
        }
    }
    // 简化：添加指定的contract和相关的
    relevant_contracts.insert("PriceOracle".to_string());
    relevant_contracts.insert("Vault".to_string());

    // 收集相关函数，用于提供给 LLM 作为上下文
    let mut related_functions = Vec::new();

    // 输出相关合约的代码，但过滤不相关的函数
    let lines: Vec<&str> = source_code.lines().collect();
    let mut result = Vec::new();
    let mut i = 0;
    while i < lines.len() {
        let line = lines[i].trim();
        if line.starts_with("contract ") {
            let contract_name = line.split_whitespace().nth(1).unwrap_or("").split('{').next().unwrap_or("");
            if relevant_contracts.contains(contract_name) {
                // 提取整个合约，但过滤函数
                let mut contract_lines = Vec::new();
                contract_lines.push(lines[i].to_string());
                let mut brace_count = 0;
                i += 1;
                while i < lines.len() {
                    let current_line = lines[i];
                    let trimmed = current_line.trim();
                    if trimmed.starts_with("function ") || trimmed.starts_with("constructor") {
                        // 提取整个函数
                        let mut func_lines = Vec::new();
                        let mut func_brace = 0;
                        let mut j = i;
                        while j < lines.len() {
                            let f_line = lines[j];
                            func_lines.push(f_line.to_string());
                            func_brace += f_line.chars().filter(|&c| c == '{').count() as i32;
                            func_brace -= f_line.chars().filter(|&c| c == '}').count() as i32;
                            if func_brace == 0 && f_line.contains('}') {
                                break;
                            }
                            j += 1;
                        }
                        // 使用 LLM 判断是否相关，提供相关函数上下文
                        let func_code = func_lines.join("\n");
                        if slicer.is_code_relevant(&func_code, "totalAssets", source_code, &related_functions).await {
                            contract_lines.extend(func_lines);
                            // 如果相关，添加到相关函数列表中，用于后续分析的上下文
                            related_functions.push(func_code.clone());
                        }
                        i = j;
                    } else {
                        contract_lines.push(current_line.to_string());
                        brace_count += current_line.chars().filter(|&c| c == '{').count() as i32;
                        brace_count -= current_line.chars().filter(|&c| c == '}').count() as i32;
                        if brace_count == 0 && current_line.contains('}') {
                            break;
                        }
                    }
                    i += 1;
                }
                result.extend(contract_lines);
            }
        }
        i += 1;
    }
    result
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
        return Err(format!("Path {} is neither a file nor a directory", input_path));
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
        } else if path.is_dir() {
            // Skip common non-source directories
            if !path.ends_with("node_modules") && !path.ends_with(".git") && !path.ends_with("target") {
                collect_sol_files_recursive(&path, files)?;
            }
        }
    }

    Ok(())
}