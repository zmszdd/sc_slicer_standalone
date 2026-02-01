//!
//! SC Slicer - Solidity 代码切片工具
//!
//! 命令行入口程序，负责解析用户参数、调用代码分析器
//! 和语义切片器，对 Solidity 智能合约进行安全分析
//! 和代码切片。
//!
//! ## 架构设计：AST分析 vs 文本处理
//!
//! ### 核心原则：
//! - **决策层（AST）**：使用AST/PDG分析结果来判断语义相关性
//! - **表示层（文本）**：保留原始代码格式（缩进、注释、空行）
//!
//! ### 为什么需要文本处理？
//! AST虽然提供准确的语法结构，但重建代码会丢失：
//! - 原始缩进和格式
//! - 注释位置和内容
//! - 空行和代码组织
//!
//! ### 分层架构：
//! 1. **AST分析层**：
//!    - `ContractRegistry`: 合约→函数映射（来自AST）
//!    - `PDG`: 数据流和控制流分析（来自AST）
//!    - `relevant_functions`: 通过PDG切片得到（基于AST）
//!
//! 2. **文本重建层**：
//!    - `extract_contract_name()`: 从文本提取名称（用于格式保留）
//!    - `is_function_start()`: 文本模式匹配（辅助定位）
//!    - 最终验证：通过`relevant_functions.contains()`检查（回到AST）
//!
//! ### 改进历史：
//! - v1: 纯文本匹配（is_interface_only_function使用正则）❌
//! - v2: AST决策 + 文本表示（当前版本）✅
//!

use clap::{Arg, Command};
use std::fs;
use std::fs::OpenOptions;
use std::io::Write;
use std::ffi::OsStr;
use std::path::Path;

mod analyzer;
pub mod semantic_slicer;
pub mod noise_reduction;
pub mod llm_completion;
// pub mod sol_resurrect; // TODO: 需要适配solar AST的具体结构

use crate::analyzer::AnalysisResult;
use crate::noise_reduction::NoiseReductionPipeline;
use crate::semantic_slicer::SemanticGraphAdapter;
use crate::llm_completion::LLMCompletionPipeline;
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
    
    // Function-Level CHSS 扩展方法
    
    fn get_all_call_edges(&self) -> Vec<semantic_slicer::CallEdge> {
        use crate::analyzer::NodeKind;
        
        let mut edges = Vec::new();
        let mut edge_id = 0;
        
        // 遍历所有节点，找出函数调用
        for (&node_id, node) in &self.analysis.program_dependency_graph.nodes {
            // 识别函数调用节点
            let is_function_call = matches!(
                node.kind, 
                NodeKind::FunctionCall | NodeKind::ExternalCall
            );
            
            if !is_function_call {
                continue;
            }
            
            // 提取调用方函数名
            let caller = node.function_context.clone().unwrap_or_else(|| "global".to_string());
            
            // 从label中提取被调用方函数名
            let callee = self.extract_callee_name(&node.label);
            
            // 获取调用处源代码
            let code_line = self.get_node_source(node_id);
            
            // 检测返回值是否被使用（简化：检查是否有赋值符号）
            let return_var_used = code_line.contains('=') && 
                                   !code_line.trim().starts_with("//");
            
            // 检测是否在require/if中（简化：检查控制依赖边）
            let is_in_require = self.is_in_control_context(node_id);
            
            // 查找被调用函数的节点ID
            let callee_id = self.find_function_entry_node(&callee);
            
            edges.push(semantic_slicer::CallEdge {
                id: edge_id,
                caller: caller.clone(),
                callee: callee.clone(),
                caller_id: node_id,
                callee_id: callee_id.unwrap_or(node_id), // 如果找不到，使用调用节点自身
                code_line: code_line.clone(),
                return_var_used,
                is_in_require,
                static_score: 0,
                decision: semantic_slicer::EdgeDecision::AskLLM,
            });
            
            edge_id += 1;
        }
        
        edges
    }
    
    fn get_function_code(&self, func_id: usize) -> String {
        // 尝试获取完整函数定义
        if let Some(node) = self.get_node_info(func_id) {
            if let Some(ref func_name) = node.function_context {
                // 在源代码中查找这个函数的完整定义
                return self.extract_full_function_by_name(func_name);
            }
        }
        
        // 降级：返回节点源码
        self.get_node_source(func_id)
    }
    
    fn get_function_name(&self, node_id: usize) -> Option<String> {
        // 从节点信息中提取函数名
        if let Some(node) = self.get_node_info(node_id) {
            node.function_context.clone()
        } else {
            None
        }
    }
    
    fn get_contract_for_function(&self, func_id: usize) -> Option<String> {
        // 方案2: 使用AST信息 - 直接从PDG节点的contract_context字段获取
        if let Some(node) = self.get_node_info(func_id) {
            if let Some(ref contract) = node.contract_context {
                return Some(contract.clone());
            }
        }
        
        // 降级方案: 如果节点没有contract_context，从label中提取（兼容旧数据）
        if let Some(node) = self.get_node_info(func_id) {
            // label格式: "entry: ContractName.FunctionName" 或 "storage: ContractName.VarName"
            if let Some(colon_pos) = node.label.find(':') {
                let after_colon = &node.label[colon_pos + 1..].trim();
                if let Some(dot_pos) = after_colon.find('.') {
                    let contract_name = &after_colon[..dot_pos];
                    return Some(contract_name.to_string());
                }
            }
        }
        
        None
    }
    
    // ===== AST-Level Coverage & Taint Tracking Extensions =====
    
    fn get_function_calls_in_code(&self, code: &str) -> Vec<semantic_slicer::FunctionCallInfo> {
        use regex::Regex;
        let mut calls = Vec::new();
        
        // 正则模式：匹配函数调用
        // 1. 外部调用: obj.func(...)
        // 2. 内部调用: func(...)
        let external_pattern = Regex::new(r"(\w+)\.(\w+)\s*\(").unwrap();
        let internal_pattern = Regex::new(r"\b(\w+)\s*\(").unwrap();
        
        // 提取外部调用
        for cap in external_pattern.captures_iter(code) {
            let receiver = cap.get(1).unwrap().as_str().to_string();
            let callee = cap.get(2).unwrap().as_str().to_string();
            let full_match = cap.get(0).unwrap().as_str().to_string();
            
            // 过滤掉Solidity关键字
            if !self.is_keyword(&callee) {
                calls.push(semantic_slicer::FunctionCallInfo {
                    callee: callee.clone(),
                    is_external: true,
                    receiver: Some(receiver),
                    code_snippet: full_match,
                });
            }
        }
        
        // 提取内部调用（过滤掉已经识别的外部调用）
        let external_set: std::collections::HashSet<String> = calls
            .iter()
            .map(|c| c.code_snippet.clone())
            .collect();
        
        for cap in internal_pattern.captures_iter(code) {
            let callee = cap.get(1).unwrap().as_str().to_string();
            let full_match = cap.get(0).unwrap().as_str().to_string();
            
            // 过滤：关键字、已识别的外部调用、类型转换
            if !self.is_keyword(&callee) 
                && !external_set.contains(&full_match)
                && !matches!(callee.as_str(), "uint256" | "address" | "bytes32" | "uint" | "int")
            {
                calls.push(semantic_slicer::FunctionCallInfo {
                    callee: callee.clone(),
                    is_external: false,
                    receiver: None,
                    code_snippet: full_match,
                });
            }
        }
        
        calls
    }
    
    fn get_vm_store_accesses(&self, code: &str) -> Vec<semantic_slicer::VmStoreInfo> {
        use regex::Regex;
        let mut accesses = Vec::new();
        
        // 正则模式：vm.store(address, slot, value)
        // 支持多行和空格变化
        let pattern = Regex::new(
            r"vm\.store\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)"
        ).unwrap();
        
        for cap in pattern.captures_iter(code) {
            let addr_expr = cap.get(1).unwrap().as_str().trim().to_string();
            let slot_expr = cap.get(2).unwrap().as_str().trim().to_string();
            let value_expr = cap.get(3).unwrap().as_str().trim().to_string();
            let full_match = cap.get(0).unwrap().as_str().to_string();
            
            accesses.push(semantic_slicer::VmStoreInfo {
                target_address: addr_expr,
                slot_expr: slot_expr.clone(),
                value_expr,
                inferred_var: self.infer_variable_from_slot(&slot_expr),
                code_snippet: full_match,
            });
        }
        
        accesses
    }
    
    fn infer_variable_from_slot(&self, slot_expr: &str) -> Option<String> {
        use regex::Regex;
        
        // 策略1: keccak256("varName") -> varName
        if let Ok(re) = Regex::new(r#"keccak256\s*\(\s*["']([^"']+)["']\s*\)"#) {
            if let Some(cap) = re.captures(slot_expr) {
                return Some(cap.get(1)?.as_str().to_string());
            }
        }
        
        // 策略2: slot_XXX -> XXX (常见命名惯例)
        if let Some(stripped) = slot_expr.strip_prefix("slot_") {
            return Some(stripped.to_string());
        }
        
        // 策略3: 常量槽位映射（Solidity存储布局）
        // 第一个状态变量在槽位0，第二个在槽位1，etc.
        // 这需要合约上下文，暂时简化处理
        if slot_expr == "0" || slot_expr == "0x0" {
            return Some("first_state_var".to_string());
        }
        
        // 策略4: keccak256(abi.encodePacked(...)) mapping推断
        if slot_expr.contains("encodePacked") {
            // 尝试提取mapping名称（通常是最后一个参数）
            if let Some(last_arg) = slot_expr.split(',').last() {
                let trimmed = last_arg.trim().trim_end_matches(')');
                if let Some(var) = trimmed.strip_prefix("slot_") {
                    return Some(format!("mapping_{}", var));
                }
            }
        }
        
        None
    }
}

// PdgAdapter 的辅助方法（不属于trait）
impl<'a> PdgAdapter<'a> {
    // 从label中提取被调用函数名
    fn extract_callee_name(&self, label: &str) -> String {
        if let Some(stripped) = label.strip_prefix("external: ") {
            stripped.split('.').last().unwrap_or(stripped).to_string()
        } else if let Some(stripped) = label.strip_prefix("call: ") {
            stripped.to_string()
        } else if label.contains('.') {
            label.split('.').last().unwrap_or(label).to_string()
        } else {
            label.to_string()
        }
    }
    
    // 检查节点是否在控制上下文中
    fn is_in_control_context(&self, node_id: usize) -> bool {
        use crate::analyzer::EdgeKind;
        
        for edge in &self.analysis.program_dependency_graph.edges {
            if edge.to == node_id && matches!(edge.kind, EdgeKind::ControlDependency) {
                if let Some(control_node) = self.analysis.program_dependency_graph.nodes.get(&edge.from) {
                    let label_lower = control_node.label.to_lowercase();
                    if label_lower.contains("require") || 
                       label_lower.contains("assert") || 
                       label_lower.contains("if") {
                        return true;
                    }
                }
            }
        }
        false
    }
    
    // 查找函数入口节点
    fn find_function_entry_node(&self, func_name: &str) -> Option<usize> {
        for (&node_id, node) in &self.analysis.program_dependency_graph.nodes {
            if let Some(ref context) = node.function_context {
                if context == func_name {
                    return Some(node_id);
                }
            }
        }
        None
    }
    
    // 从源代码中提取完整函数定义
    fn extract_full_function_by_name(&self, func_name: &str) -> String {
        let lines: Vec<&str> = self.source_code.lines().collect();
        let mut result = String::new();
        let mut i = 0;
        
        while i < lines.len() {
            let line = lines[i];
            
            if line.contains("function") && line.contains(func_name) {
                let mut brace_count = 0;
                let mut j = i;
                
                while j < lines.len() {
                    let current = lines[j];
                    result.push_str(current);
                    result.push('\n');
                    
                    brace_count += current.chars().filter(|&c| c == '{').count() as i32;
                    brace_count -= current.chars().filter(|&c| c == '}').count() as i32;
                    
                    if brace_count == 0 && current.contains('}') {
                        break;
                    }
                    j += 1;
                }
                
                return result;
            }
            
            i += 1;
        }
        
        String::new()
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
        .arg(
            Arg::new("model")
                .help("LLM model name (default: deepseek-ai/DeepSeek-V3.2)")
                .long("model")
                .value_name("MODEL")
                .default_value("deepseek-ai/DeepSeek-V3.2"),
        )
        .arg(
            Arg::new("two_phase")
                .help("Use two-phase processing: static slice first, then semantic analysis")
                .long("two-phase")
                .action(clap::ArgAction::SetTrue),
        )
        .arg(
            Arg::new("llm_threshold")
                .help("Minimum static score to trigger LLM analysis (0-100, default 30)")
                .long("llm-threshold")
                .value_name("SCORE")
                .default_value("30"),
        )
        .arg(
            Arg::new("parallel")
                .help("Enable parallel LLM calls (default: 4 concurrent requests)")
                .long("parallel")
                .action(clap::ArgAction::SetTrue),
        )
        .arg(
            Arg::new("max_concurrent")
                .help("Maximum concurrent LLM requests (default: 4)")
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
                .help("Enable LLM three-stage completion pipeline (analyze->complete->fix). Universal: works for any contract/variable by analyzing slice target context.")
                .long("llm-completion")
                .action(clap::ArgAction::SetTrue),
        )
        .arg(
            Arg::new("resurrect")
                .help("Enable AST-based code resurrection to reconstruct fragmented slices into compilable code")
                .long("resurrect")
                .action(clap::ArgAction::SetTrue),
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
    let use_two_phase = matches.get_flag("two_phase");
    let use_parallel = matches.get_flag("parallel");
    let use_prefilter = matches.get_flag("prefilter");
    let aggressive_cleanup = matches.get_flag("aggressive_noise_reduction");
    let use_llm_completion = matches.get_flag("llm_completion");
    let max_level: usize = matches.get_one::<String>("max_level")
        .and_then(|s| s.parse().ok())
        .unwrap_or(3)
        .min(10);
    let llm_threshold: u8 = matches.get_one::<String>("llm_threshold")
        .and_then(|s| s.parse().ok())
        .unwrap_or(30)
        .min(100);
    let max_concurrent: usize = matches.get_one::<String>("max_concurrent")
        .and_then(|s| s.parse().ok())
        .unwrap_or(4)
        .max(1)
        .min(20);
    let cache_file = matches.get_one::<String>("cache_file").map(|s| s.as_str());
    let api_key_from_arg = matches.get_one::<String>("api_key").map(|s| s.as_str()).unwrap_or("");
    let api_key = if !api_key_from_arg.is_empty() {
        api_key_from_arg.to_string()
    } else {
        std::env::var("OPENAI_API_KEY").unwrap_or_else(|_| String::new())
    };
    let base_url = std::env::var("OPENAI_BASE_URL").unwrap_or_else(|_| "https://api.deepseek.com".to_string());
    let model_name = matches.get_one::<String>("model").unwrap().to_string();

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
        // 使用目标导向的分析
        Ok(analyzer::analyze_asts_targeted(&all_asts, &combined_source, contract_name, function_name, variable_name))
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
        
        if use_two_phase {
            println!("🔄 Using two-phase processing for large files...");
            if use_parallel {
                println!("⚡ Parallel processing enabled: {} concurrent requests", max_concurrent);
            }
            if use_prefilter {
                println!("🔍 Pre-filtering enabled");
            }
            if let Some(cache) = cache_file {
                println!("💾 Using cache file: {}", cache);
            }
            
            // 第一阶段：快速静态切片
            println!("📍 Phase 1: Static slicing to identify relevant code...");
            let static_slice = analyzer::get_source_slice(&analysis, &combined_source, contract_name, function_name, variable_name, exclude_libs, include_types);
            println!("✅ Phase 1 complete: {} code blocks identified", static_slice.len());
            
            // 提取静态切片中的合约和函数信息
            let (phase1_contracts, phase1_functions) = extract_contracts_and_functions(&static_slice);
            println!("📊 Relevant contracts: {:?}", phase1_contracts);
            println!("📊 Relevant functions: {} functions", phase1_functions.len());
            
            // 三层漏斗过滤
            let filter_result = if use_prefilter {
                three_layer_filter(&phase1_contracts, variable_name)
            } else {
                // 不启用预过滤时，全部进入白名单
                ThreeLayerFilterResult {
                    blacklist: std::collections::HashSet::new(),
                    whitelist: phase1_contracts.clone(),
                    graylist: std::collections::HashSet::new(),
                }
            };
            
            // 如果有灰名单，调用LLM仲裁
            let llm_kept = if !filter_result.graylist.is_empty() {
                match llm_arbitrate_graylist(
                    &filter_result.graylist,
                    &api_key,
                    &base_url,
                    &model_name
                ).await {
                    Ok(kept) => kept,
                    Err(e) => {
                        eprintln!("⚠️  LLM arbitration failed: {}, keeping all graylist contracts", e);
                        filter_result.graylist.clone()
                    }
                }
            } else {
                std::collections::HashSet::new()
            };
            
            // 合并最终过滤结果：白名单 + LLM保留的灰名单
            let mut filtered_contracts = filter_result.whitelist.clone();
            filtered_contracts.extend(llm_kept);
            
            println!("📊 Final filtered contracts: {} contracts\n", filtered_contracts.len());
            
            // 第二阶段：只对相关代码进行语义分析
            println!("📍 Phase 2: Semantic analysis on relevant code only...");
            let adapter = PdgAdapter { analysis: &analysis, source_code: &combined_source };
            let model = model_name.clone();
            let mut slicer = crate::semantic_slicer::SemanticSlicer::new_with_options(
                &adapter, 
                api_key.to_string(), 
                base_url.to_string(), 
                model, 
                llm_threshold,
                use_parallel,
                max_concurrent,
                cache_file.map(|s| s.to_string())
            );
            
            let sink_nodes = find_sink_nodes(&analysis, variable_name);
            
            // 使用新的函数级混合切片（CHSS），传入Phase 1过滤的合约列表
            let slice_nodes = slicer.run_slicing(sink_nodes).await;
            println!("✅ Phase 2 complete: Function-Level CHSS finished");
            
            // 转换为 Vec<String> 格式以保持兼容性
            get_source_from_nodes(&mut slicer, &analysis, &combined_source, &slice_nodes, contract_name, function_name, variable_name, exclude_libs, include_types, max_level, aggressive_cleanup).await
        } else {
            // 使用语义切片（传统单阶段）- 保留旧逻辑作为后备
            let adapter = PdgAdapter { analysis: &analysis, source_code: &combined_source };
            let model = model_name.clone();
            let mut slicer = crate::semantic_slicer::SemanticSlicer::new_with_threshold(&adapter, api_key.to_string(), base_url.to_string(), model, llm_threshold);
            let sink_nodes = find_sink_nodes(&analysis, variable_name);
            
            // 使用语义切片
            let slice_nodes = slicer.run_slicing(sink_nodes).await;
            get_source_from_nodes(&mut slicer, &analysis, &combined_source, &slice_nodes, contract_name, function_name, variable_name, exclude_libs, include_types, max_level, aggressive_cleanup).await
        }
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

    // ⏭️ 跳过 S1.2 PoC 质量分析，直接输出切片结果
    // 如需启用质量分析，取消下面的注释
    /*
    if use_semantic {
        println!("🤖 Performing S1.2 PoC Quality Analysis...");
        let slice_code = slice.join("\n");
        
        let adapter = PdgAdapter { analysis: &analysis, source_code: &combined_source };
        let model = model_name.clone();
        let slicer = crate::semantic_slicer::SemanticSlicer::new_with_options(
            &adapter, 
            api_key.to_string(), 
            base_url.to_string(), 
            model, 
            llm_threshold,
            use_parallel,
            max_concurrent,
            None
        );
        
        match slicer.analyze_poc_quality(&slice_code).await {
            Ok(report) => {
                println!("\n📊 S1.2 PoC Quality Analysis Report:");
                println!("{}", "=".repeat(60));
                println!("{}", report);
                println!("{}", "=".repeat(60));
                
                writeln!(log_file, "\n📊 S1.2 PoC Quality Analysis Report:")?;
                writeln!(log_file, "{}", "=".repeat(60))?;
                writeln!(log_file, "{}", report)?;
                writeln!(log_file, "{}", "=".repeat(60))?;
            },
            Err(e) => {
                eprintln!("❌ Failed to perform PoC quality analysis: {}", e);
            }
        }
    }
    */

    // 🔧 新增功能：代码补全（在输出前检查是否需要补全缺失的类型）
    let slice_code = slice.join("\n");
    let final_output = if use_semantic {
        println!("🔧 Checking for missing type definitions...");
        let adapter = PdgAdapter { analysis: &analysis, source_code: &combined_source };
        let model = model_name.clone();
        let slicer = crate::semantic_slicer::SemanticSlicer::new_with_options(
            &adapter, 
            api_key.to_string(), 
            base_url.to_string(), 
            model, 
            llm_threshold,
            use_parallel,
            max_concurrent,
            None
        );
        
        match slicer.complete_code(&slice_code, &combined_source).await {
            Ok(completed_code) => {
                println!("✅ Code completion finished");
                completed_code
            },
            Err(e) => {
                eprintln!("⚠️  Code completion failed: {}, using original slice", e);
                slice_code
            }
        }
    } else {
        slice_code
    };

    // LLM三阶段补全（如果启用）
    let final_output = if use_llm_completion {
        match LLMCompletionPipeline::new() {
            Ok(pipeline) => {
                // 传递源文件路径（使用第一个.sol文件作为源码）
                let pipeline_with_source = if !file_paths.is_empty() {
                    pipeline.with_source_file(file_paths[0].clone())
                } else {
                    pipeline
                };
                
                match pipeline_with_source.run_completion_pipeline(&final_output) {
                    Ok(completed_code) => {
                        writeln!(log_file, "✅ LLM补全成功")?;
                        completed_code
                    },
                    Err(e) => {
                        writeln!(log_file, "⚠️  LLM补全失败: {}, 使用原始代码", e)?;
                        final_output
                    }
                }
            },
            Err(e) => {
                writeln!(log_file, "⚠️  LLM初始化失败: {}, 跳过补全", e)?;
                final_output
            }
        }
    } else {
        final_output
    };

    // AST-based Code Resurrection（功能开发中）
    let use_resurrect = matches.get_flag("resurrect");
    let final_output = if use_resurrect {
        eprintln!("⚠️  Code resurrection feature is under development");
        eprintln!("   Current status: AST pattern matching needs adjustment for solar crate");
        eprintln!("   See RESURRECTION_README.md for details");
        writeln!(log_file, "⚠️  Resurrection feature not yet available")?;
        final_output
    } else {
        final_output
    };

    if let Some(output_file) = output_file {
        fs::write(output_file, final_output.clone()).expect("Failed to write to file");
        writeln!(log_file, "✅ Results written to {}", output_file)?;
    } else {
        writeln!(log_file, "🔍 Source Code Slice Analysis")?;
        writeln!(log_file, "📁 Input: {}", input_path)?;
        writeln!(log_file, "🏢 Contract: {}", contract_name)?;
        writeln!(log_file, "⚡ Function: {}", if function_name.is_empty() { "All functions" } else { function_name })?;
        writeln!(log_file, "📊 Variable: {}", variable_name)?;
        writeln!(log_file, "🎯 Slice Level: {}", slice_level)?;
        writeln!(log_file, "📋 Slice Results ({} lines):", final_output.lines().count())?;
        writeln!(log_file, "{}", "=".repeat(60))?;

        for line in final_output.lines() {
            writeln!(log_file, "{}", line)?;
        }

        writeln!(log_file, "{}", "=".repeat(60))?;
        writeln!(log_file, "✅ Analysis completed successfully!")?;
    }
    Ok(())
}

fn find_sink_nodes(analysis: &AnalysisResult, variable_name: &str) -> Vec<usize> {
    let mut sinks = Vec::new();
    println!("🔍 Looking for StorageWrite/VariableWrite nodes for variable: {}", variable_name);

    // 遍历graph的节点索引，找到对应的存储节点或变量节点
    for node_index in analysis.program_dependency_graph.graph.node_indices() {
        if let Some(&stored_node_id) = analysis.program_dependency_graph.graph.node_weight(node_index) {
            if let Some(node) = analysis.program_dependency_graph.nodes.get(&stored_node_id) {
                // 1. 匹配变量写入
                if matches!(node.kind, crate::analyzer::NodeKind::StorageWrite(ref v) if v == variable_name) ||
                   matches!(node.kind, crate::analyzer::NodeKind::VariableWrite(ref v) if v == variable_name) {
                    println!("✅ Found sink node {} (graph index {}) : kind={:?}, label='{}', function_context={:?}",
                        stored_node_id, node_index.index(), node.kind, node.label, node.function_context);
                    sinks.push(node_index.index()); // 返回graph节点索引
                }
                // 2. 匹配断言节点 (ConstraintNode) - 如果变量名是 "ASSERT" 或 "REQUIRE"
                else if (variable_name == "ASSERT" || variable_name == "REQUIRE") && 
                        matches!(node.kind, crate::analyzer::NodeKind::ConstraintNode) {
                    println!("✅ Found assertion sink node {} (graph index {}) : kind={:?}, label='{}'",
                        stored_node_id, node_index.index(), node.kind, node.label);
                    sinks.push(node_index.index());
                }
            }
        }
    }

    println!("📊 Total sink nodes found: {}", sinks.len());
    sinks
}

async fn get_source_from_nodes<'a>(slicer: &mut crate::semantic_slicer::SemanticSlicer<'a, PdgAdapter<'a>>, analysis: &AnalysisResult, source_code: &str, slice_nodes: &std::collections::HashSet<usize>, contract: &str, function: &str, variable: &str, exclude_libs: bool, include_types: bool, max_level: usize, aggressive_cleanup: bool) -> Vec<String> {
    // 🔥 使用AST分析结果，而非字符串解析
    // 从slice_nodes中提取相关的合约和函数（基于PDG分析）
    let mut relevant_contracts = std::collections::HashSet::new();
    let mut relevant_functions = std::collections::HashSet::new();

    for &node_id in slice_nodes {
        if let Some(&stored_node_id) = analysis.program_dependency_graph.graph.node_weight(petgraph::graph::NodeIndex::new(node_id)) {
            if let Some(node) = analysis.program_dependency_graph.nodes.get(&stored_node_id) {
                // 提取函数上下文（来自AST分析）
                if let Some(func_name) = &node.function_context {
                    relevant_functions.insert(func_name.clone());
                }
            }
        }
    }

    // 🔥 从ContractRegistry（AST分析结果）中找到相关的合约
    // 而非通过字符串匹配
    for (contract_name, functions) in &analysis.contract_registry.function_map {
        for func_name in functions.keys() {
            if relevant_functions.contains(func_name) {
                relevant_contracts.insert(contract_name.clone());
            }
        }
    }

    // 确保目标合约被包含
    relevant_contracts.insert(contract.to_string());

    // 🔥 改进0：提取状态变量的类型映射（用于追踪外部调用）
    let var_type_map = extract_variable_type_mapping(source_code, &analysis.contract_registry);
    println!("📋 Variable type mapping: {} variables found", var_type_map.len());
    
    // 🔥 改进0.1：从外部调用中识别被调用的合约类型
    let mut external_contract_types = std::collections::HashSet::new();
    for &node_id in slice_nodes {
        if let Some(&stored_node_id) = analysis.program_dependency_graph.graph.node_weight(petgraph::graph::NodeIndex::new(node_id)) {
            if let Some(node) = analysis.program_dependency_graph.nodes.get(&stored_node_id) {
                // 检测外部调用节点
                if matches!(node.kind, crate::analyzer::NodeKind::ExternalCall) || 
                   matches!(node.kind, crate::analyzer::NodeKind::TaintSource) {
                    // 从label中提取接收者变量名
                    // 格式如: "external: accountant.computeNAV" 或 "receiver.method"
                    let receiver_var = extract_receiver_variable(&node.label);
                    if let Some(var_name) = receiver_var {
                        if let Some(contract_type) = var_type_map.get(&var_name) {
                            println!("🔍 External call detected: {}.xxx -> type: {}", var_name, contract_type);
                            external_contract_types.insert(contract_type.clone());
                        }
                    }
                }
            }
        }
    }
    
    // 🔥 改进0.2：强制包含被调用的外部合约及其所有函数
    for contract_type in &external_contract_types {
        relevant_contracts.insert(contract_type.clone());
        println!("✅ Force-included external contract: {}", contract_type);
        
        // 包含该合约的所有函数（因为我们不确定哪些会被调用）
        if let Some(functions) = analysis.contract_registry.function_map.get(contract_type) {
            for func_name in functions.keys() {
                relevant_functions.insert(func_name.clone());
                println!("  ↳ Including function: {}", func_name);
            }
        }
    }

    // 🔥 改进1：强制包含测试设置函数（setUp, constructor等）
    const TEST_SETUP_FUNCTIONS: &[&str] = &["setUp", "beforeEach", "constructor"];
    for setup_func in TEST_SETUP_FUNCTIONS {
        for functions in analysis.contract_registry.function_map.values() {
            if functions.contains_key(*setup_func) {
                relevant_functions.insert(setup_func.to_string());
                println!("✅ Force-included test setup function: {}", setup_func);
            }
        }
    }
    
    // 🔥 改进2：追踪被调用但未实现的函数（深度调用链）
    // 这解决了 "computeNAV 实现缺失" 的问题
    let mut iteration = 0;
    let max_iterations = 5; // 防止无限循环
    let initial_size = relevant_functions.len();
    
    loop {
        iteration += 1;
        if iteration > max_iterations {
            break;
        }
        
        let current_funcs: Vec<String> = relevant_functions.iter().cloned().collect();
        let mut new_called_funcs = std::collections::HashSet::new();
        
        for func_name in &current_funcs {
            let called = find_called_functions(analysis, func_name);
            for called_func in called {
                if !relevant_functions.contains(&called_func) {
                    new_called_funcs.insert(called_func);
                }
            }
        }
        
        if new_called_funcs.is_empty() {
            break;
        }
        
        println!("🔍 Iteration {}: Found {} additional called functions", iteration, new_called_funcs.len());
        relevant_functions.extend(new_called_funcs);
    }
    
    println!("🎯 Deep call chain tracking: {} -> {} functions (+{})", 
        initial_size, relevant_functions.len(), relevant_functions.len() - initial_size);
    
    // 🔥 改进3：构建函数级层级系统（以函数为最小粒度）
    // 从relevant_functions（PDG切片的核心函数）开始，向外扩展调用层级
    let (mut function_levels, contract_levels) = build_function_level_hierarchy(analysis, &relevant_functions);
    
    // 🔥 扩展：将层级系统内的所有函数加入relevant_functions（基于max_level过滤）
    for (func_name, &level) in &function_levels {
        if level <= max_level {
            relevant_functions.insert(func_name.clone());
        }
    }
    
    println!("🎯 Initial relevant functions (from PDG): {} functions", initial_size);
    println!("📊 Function hierarchy: {} functions across {} levels", function_levels.len(), function_levels.values().max().unwrap_or(&0) + 1);
    println!("📊 Contract hierarchy (derived): {:?}", contract_levels);
    println!("🎯 Final expanded functions (with hierarchy, max_level={}): {} functions", max_level, relevant_functions.len());

    // 直接从源码中提取相关的合约和类型定义（函数级别过滤）
    let lines: Vec<&str> = source_code.lines().collect();
    let mut result = Vec::new();
    let mut i = 0;
    
    // 🔥 标记是否在文件头部（前50行用于SPDX/Pragma检测）
    let mut is_in_file_header = true;
    let mut header_line_count = 0;

    while i < lines.len() {
        let line = lines[i];
        let trimmed = line.trim();
        
        // 🔥 改进方案2：追踪文件头部（前50行用于注释清洗）
        if header_line_count < 50 {
            header_line_count += 1;
            if trimmed.starts_with("contract ") || trimmed.starts_with("library ") || trimmed.starts_with("interface ") {
                is_in_file_header = false; // 遇到第一个合约/库/接口定义，结束文件头
            }
        }

        // 检查是否是合约、库或类型定义的开始
        let is_contract_or_lib = trimmed.starts_with("contract ") || trimmed.starts_with("library ");
        let is_interface = trimmed.starts_with("interface ");
        let is_type_def = trimmed.starts_with("type ") || trimmed.starts_with("struct ") || trimmed.starts_with("enum ");

        // 🔥 跳过接口定义 - 接口只有函数声明，对分析没有用处
        if is_interface {
            // 跳过整个接口定义
            let mut brace_count: i32 = 0;
            let mut j = i;
            while j < lines.len() {
                let current_line = lines[j];
                brace_count += current_line.chars().filter(|&c| c == '{').count() as i32;
                let close_count = current_line.chars().filter(|&c| c == '}').count() as i32;
                if brace_count >= close_count {
                    brace_count -= close_count;
                } else {
                    brace_count = 0;
                }
                
                if brace_count == 0 && current_line.contains('}') {
                    i = j;
                    break;
                }
                j += 1;
            }
            i += 1;
            continue;
        }

        if is_contract_or_lib || is_type_def {
            // 提取合约/库/类型名称
            let name = if is_contract_or_lib {
                extract_contract_name(line)
            } else if is_type_def {
                extract_type_name(line)
            } else {
                String::new()
            };
            
            // 🔥 改进4：标准库检测和存根化（优先于相关性检查）
            let is_stdlib = is_standard_library_contract(&name);
            
            if is_stdlib && is_contract_or_lib {
                // 🔥 规则2：标准库存根化（输出空壳）
                println!("📚 Stdlib stubbed: {}", name);
                result.push(format!("{} {} {{}}",  // 空壳，无注释
                    if line.contains("contract") { "contract" } else { "library" },
                    name));
                
                // 跳过整个标准库合约
                let mut brace_count: i32 = 0;
                let mut j = i;
                while j < lines.len() {
                    let current_line = lines[j];
                    brace_count += current_line.chars().filter(|&c| c == '{').count() as i32;
                    let close_count = current_line.chars().filter(|&c| c == '}').count() as i32;
                    if brace_count >= close_count {
                        brace_count -= close_count;
                    } else {
                        brace_count = 0;
                    }
                    
                    if brace_count == 0 && current_line.contains('}') {
                        i = j;
                        break;
                    }
                    j += 1;
                }
                i += 1;
                continue;
            }

            // 🔥 改进方案1：在第一遍收集时先暂存所有可能的内容
            // 第二遍才根据标识符使用情况过滤类型定义
            let is_relevant_for_first_pass = if is_contract_or_lib {
                // 必须在relevant_contracts中 && (存在于层级系统中 || 是目标合约)
                // 但标准库已经在上面被存根化了
                if !relevant_contracts.contains(&name) {
                    false
                } else {
                    // 如果在层级系统中，检查层级是否在用户指定的阈值内
                    contract_levels.get(&name).map_or(false, |&level| level <= max_level)
                        || name == contract // 目标合约总是保留
                }
            } else if is_type_def {
                include_types // 第一遍先暂时保留，第二遍检查使用情况
            } else {
                false
            };
            
            let is_relevant = is_relevant_for_first_pass;

            if is_relevant {
                if is_contract_or_lib {
                    // 函数级别过滤：只提取相关函数（基于层级过滤，同时过滤接口函数）
                    let filtered_contract = extract_contract_with_functions_filtered(&lines, i, &relevant_functions, &function_levels, max_level);
                    result.push(filtered_contract);
                } else {
                    // 类型定义直接提取
                    let definition_code = extract_entire_definition(&lines, i);
                    result.push(definition_code);
                }

                // 跳过已处理的行
                let mut brace_count: i32 = 0;
                let mut j = i;
                while j < lines.len() {
                    let current_line = lines[j];
                    brace_count += current_line.chars().filter(|&c| c == '{').count() as i32;
                    let close_count = current_line.chars().filter(|&c| c == '}').count() as i32;
                    if brace_count >= close_count {
                        brace_count -= close_count;
                    } else {
                        brace_count = 0;
                    }

                    if brace_count == 0 && current_line.contains('}') {
                        i = j;
                        break;
                    }
                    j += 1;
                }
            }
        }
        i += 1;
    }

    // 🔥 改进方案1 - 第二遍：类型树摇 (Type Tree Shaking)
    println!("🌳 Starting Type Tree Shaking...");
    let initial_count = result.len();
    
    // 1. 提取所有保留代码中使用的标识符
    let used_identifiers = extract_used_identifiers(&result);
    println!("   Found {} unique identifiers in preserved code", used_identifiers.len());
    
    // 2. 过滤掉未使用的类型定义
    let mut filtered_result = Vec::new();
    let mut removed_types = Vec::new();
    
    for item in &result {
        let first_line = item.lines().next().unwrap_or("").trim();
        
        // 检查是否是类型定义
        if first_line.starts_with("struct ") || first_line.starts_with("enum ") || first_line.starts_with("type ") {
            let type_name = extract_type_name(first_line);
            
            // 🔥 规则1：强制删除 Foundry 内部类型
            if is_foundry_internal_type(&type_name) {
                removed_types.push(type_name.clone());
                println!("   🚫 Removed Foundry internal type: {}", type_name);
                continue;
            }
            
            // 检查该类型是否被使用
            if is_type_used(first_line, &used_identifiers) {
                filtered_result.push(item.clone());
            } else {
                removed_types.push(type_name.clone());
                println!("   ✂️  Removed unused type: {}", type_name);
            }
        } else {
            // 非类型定义，直接保留
            filtered_result.push(item.clone());
        }
    }
    
    println!("🌳 Type Tree Shaking complete: {} items -> {} items (-{})",
        initial_count, filtered_result.len(), initial_count - filtered_result.len());
    
    // 🔥 改进方案2：激进的注释清洗
    println!("✂️  Starting Aggressive Comment Stripping...");
    let mut cleaned_result = Vec::new();
    let mut total_comment_lines_removed = 0;
    
    for (idx, item) in filtered_result.iter().enumerate() {
        let lines_in_item: Vec<&str> = item.lines().collect();
        let mut cleaned_lines = Vec::new();
        
        // 检测是否是库文件（通过第一行判断）
        let first_line = lines_in_item.first().map(|s| s.trim()).unwrap_or("");
        
        // 🔥 改进：更精确的库检测
        let is_in_lib = first_line.starts_with("library ") || 
                        is_standard_library_contract(&extract_contract_name(first_line));
        
        // 🔥 改进：检测是否是节点模块或依赖库的合约
        let contract_name = extract_contract_name(first_line);
        let is_dependency_contract = is_standard_library_contract(&contract_name) ||
                                     contract_name.contains("Lib") ||
                                     contract_name == "Address" ||
                                     contract_name == "Ownable" ||
                                     contract_name.starts_with("ERC");
        
        let original_line_count = lines_in_item.len();
        
        // 🔥 规则3：追踪是否在函数体内部（用于区分文档注释和逻辑注释）
        let mut in_function_body = false;
        let mut brace_depth = 0;
        
        // 对每一行进行注释清洗
        for (line_idx, line) in lines_in_item.iter().enumerate() {
            let trimmed = line.trim();
            
            // 追踪大括号深度，判断是否在函数体内
            if trimmed.starts_with("function ") || trimmed.starts_with("constructor") {
                // 检查是否是单行函数声明（如接口）
                if trimmed.ends_with(";") {
                    in_function_body = false;
                } else if trimmed.contains("{") {
                    in_function_body = true;
                    brace_depth = trimmed.matches('{').count() as i32;
                    brace_depth -= trimmed.matches('}').count() as i32;
                }
            } else {
                // 更新大括号深度
                brace_depth += trimmed.matches('{').count() as i32;
                brace_depth -= trimmed.matches('}').count() as i32;
                
                if brace_depth <= 0 {
                    in_function_body = false;
                    brace_depth = 0;
                }
            }
            
            // 判断是否在文件头部（前20行，包含ASCII Art）
            let is_header_line = line_idx < 20;
            
            let cleaned_line = strip_aggressive_comments(
                line, 
                is_in_lib || is_dependency_contract, 
                is_header_line,
                in_function_body  // 🔥 新增：传递函数体内外标记
            );
            
            // 只保留非空行
            if !cleaned_line.trim().is_empty() {
                cleaned_lines.push(cleaned_line);
            }
        }
        
        let removed_count = original_line_count - cleaned_lines.len();
        total_comment_lines_removed += removed_count;
        
        if removed_count > 5 && is_in_lib {
            println!("   ✂️  Cleaned {} (lib): removed {} comment lines", contract_name, removed_count);
        }
        
        // 重组清洗后的代码块
        let cleaned_item = cleaned_lines.join("\n");
        
        // 只有非空的代码块才保留
        if !cleaned_item.trim().is_empty() {
            cleaned_result.push(cleaned_item);
        }
    }
    
    println!("✂️  Comment stripping complete: removed {} comment/blank lines total", total_comment_lines_removed);
    
    // 🔥 新增：激进的噪音削减管道（可选）
    if aggressive_cleanup {
        println!("\n🚀 Starting Advanced Noise Reduction Pipeline...");
        let mut pipeline = NoiseReductionPipeline::default();
        let result = pipeline.reduce(cleaned_result);
        
        result.stats.print_summary();
        
        result.code_blocks
    } else {
        cleaned_result
    }
}

// 🔥 提取接收者变量名
// 从 "external: accountant.computeNAV" 或 "receiver.method" 中提取 "accountant" 或 "receiver"
fn extract_receiver_variable(label: &str) -> Option<String> {
    // 移除 "external: " 前缀（如果有）
    let cleaned = if let Some(idx) = label.find("external:") {
        label[idx + 9..].trim()
    } else {
        label
    };
    
    // 查找第一个点号，提取之前的部分
    if let Some(dot_idx) = cleaned.find('.') {
        let receiver = cleaned[..dot_idx].trim();
        // 排除常见的非变量模式
        if !receiver.is_empty() && 
           !receiver.starts_with("call") &&
           !receiver.starts_with("Expr") &&
           !receiver.contains('(') {
            return Some(receiver.to_string());
        }
    }
    
    None
}

// 🔥 从源代码中提取变量类型映射
// 解析如 "PanopticVaultAccountant accountant;" 这样的声明
fn extract_variable_type_mapping(
    source_code: &str,
    contract_registry: &analyzer::ContractRegistry,
) -> std::collections::HashMap<String, String> {
    let mut var_type_map = std::collections::HashMap::new();
    
    // 收集所有已知的合约/类型名称
    let mut known_types = std::collections::HashSet::new();
    for contract_name in contract_registry.function_map.keys() {
        known_types.insert(contract_name.clone());
    }
    
    // 正则匹配变量声明（简化版）
    // 格式: ContractType variableName;
    let lines: Vec<&str> = source_code.lines().collect();
    
    for line in lines {
        let trimmed = line.trim();
        
        // 跳过注释和空行
        if trimmed.starts_with("//") || trimmed.is_empty() {
            continue;
        }
        
        // 查找类型声明模式：TypeName variableName;
        for type_name in &known_types {
            if trimmed.contains(type_name) && trimmed.contains(';') {
                // 尝试提取变量名
                // 模式: TypeName variableName;
                if let Some(type_start) = trimmed.find(type_name) {
                    let after_type = &trimmed[type_start + type_name.len()..];
                    
                    // 提取变量名（在类型名之后，分号之前）
                    if let Some(semicolon) = after_type.find(';') {
                        let var_part = after_type[..semicolon].trim();
                        
                        // 清理变量名（移除可见性修饰符等）
                        let var_name = var_part
                            .split_whitespace()
                            .last()
                            .unwrap_or("")
                            .trim();
                        
                        if !var_name.is_empty() && is_valid_identifier(var_name) {
                            var_type_map.insert(var_name.to_string(), type_name.clone());
                        }
                    }
                }
            }
        }
    }
    
    var_type_map
}

// 检查是否是有效的标识符
fn is_valid_identifier(s: &str) -> bool {
    !s.is_empty() && 
    s.chars().all(|c| c.is_alphanumeric() || c == '_') &&
    !s.chars().next().unwrap().is_numeric()
}

// 🔥 改进方案1：从保留函数的源代码中提取所有标识符
fn extract_used_identifiers(source_lines: &[String]) -> std::collections::HashSet<String> {
    let mut identifiers = std::collections::HashSet::new();
    
    // 连接所有源代码
    let full_source = source_lines.join("\n");
    
    // 提取所有可能的标识符（字母数字和下划线组合）
    let mut current_identifier = String::new();
    
    for ch in full_source.chars() {
        if ch.is_alphanumeric() || ch == '_' {
            current_identifier.push(ch);
        } else {
            if !current_identifier.is_empty() {
                // 过滤掉纯数字和 Solidity 关键字
                if is_valid_identifier(&current_identifier) && !is_solidity_keyword(&current_identifier) {
                    identifiers.insert(current_identifier.clone());
                }
                current_identifier.clear();
            }
        }
    }
    
    // 处理最后一个标识符
    if !current_identifier.is_empty() && is_valid_identifier(&current_identifier) {
        identifiers.insert(current_identifier);
    }
    
    identifiers
}

// 检查是否是 Solidity 关键字
fn is_solidity_keyword(s: &str) -> bool {
    const KEYWORDS: &[&str] = &[
        "function", "contract", "library", "interface", "struct", "enum",
        "mapping", "address", "uint256", "uint128", "uint64", "uint32",
        "int256", "int128", "bool", "string", "bytes", "bytes32",
        "public", "private", "internal", "external", "view", "pure",
        "payable", "constant", "immutable", "storage", "memory", "calldata",
        "return", "returns", "if", "else", "for", "while", "do",
        "require", "assert", "revert", "emit", "event", "modifier",
        "constructor", "fallback", "receive", "virtual", "override",
        "abstract", "is", "new", "delete", "this", "super", "true", "false"
    ];
    KEYWORDS.contains(&s)
}

// 🔥 规则1：Foundry/Hardhat 内部类型黑名单
fn is_foundry_internal_type(type_name: &str) -> bool {
    const FOUNDRY_BLACKLIST: &[&str] = &[
        // Forge-std 内部类型
        "RawTx1559", "TxLegacy", "TxEIP2930", "TxEIP4844",
        "Receipt", "Log", "Chain", "Wallet",
        "FuzzSelector", "FuzzInterface", "FuzzInterfaceFunction",
        "ScriptArtifact", "Broadcast", "BroadcastTxSummary",
        "AccountAccess", "StorageAccess", "GasMetering",
        "Rpc", "RpcUrls", "FsMetadata",
        // Hardhat Console 内部类型
        "ConsoleLog", "HardhatConsole",
        // Foundry 测试框架类型
        "StdInvariant", "InvariantTest", "FuzzTest",
    ];
    
    FOUNDRY_BLACKLIST.iter().any(|&blacklisted| type_name == blacklisted)
}

// 🔥 改进方案1：检查类型定义是否被使用
fn is_type_used(type_def_line: &str, used_identifiers: &std::collections::HashSet<String>) -> bool {
    // 提取类型名称
    let type_name = if type_def_line.trim().starts_with("struct ") {
        extract_type_name(type_def_line)
    } else if type_def_line.trim().starts_with("enum ") {
        extract_type_name(type_def_line)
    } else if type_def_line.trim().starts_with("type ") {
        extract_type_name(type_def_line)
    } else {
        return true; // 非类型定义，保留
    };
    
    // 检查类型名是否在使用的标识符集合中
    used_identifiers.contains(&type_name)
}

// 🔥 改进方案2：激进的注释清洗
// 🔥 规则3：区分文档注释和逻辑注释
fn strip_aggressive_comments(line: &str, is_in_lib: bool, is_file_header: bool, in_function_body: bool) -> String {
    let trimmed = line.trim();
    
    // 1. 文件头清洗：删除 SPDX、Pragma 附近的注释
    if is_file_header {
        if trimmed.starts_with("//") {
            // 🔥 改进：检测ASCII Art（包含特殊字符）
            let has_ascii_art = trimmed.chars().any(|c| {
                "▲▼◄►│┌┐└┘├┤┬┴┼─═║╔╗╚╝╠╣╦╩╬".contains(c)
            });
            
            if has_ascii_art {
                return String::new(); // 删除ASCII Art注释
            }
            
            // 删除文件头常见注释模式
            if trimmed.starts_with("// SPDX") || 
               trimmed.starts_with("// pragma") ||
               trimmed.starts_with("// solc") {
                return String::new();
            }
        }
        
        // 删除多行注释开始标记
        if trimmed.starts_with("/*") || trimmed.starts_with("/**") {
            return String::new();
        }
    }
    
    // 2. 库文件清洗：激进删除所有文档注释（漏洞分析不需要库文档）
    if is_in_lib {
        // 🔥 激进：删除所有 /// 文档注释
        if trimmed.starts_with("///") {
            return String::new();
        }
        
        // 🔥 激进：删除所有 /** ... */ 多行文档注释
        if trimmed.starts_with("/**") || trimmed.starts_with("*/") {
            return String::new();
        }
        
        // 🔥 激进：删除多行注释内的所有 * 开头行（不仅是@标签）
        if trimmed.starts_with("*") {
            return String::new();
        }
        
        // 删除单行文档注释
        if trimmed.starts_with("// @") {
            return String::new();
        }
    }
    
    // 3. ASCII Art 和装饰性注释清洗（全局）
    if trimmed.starts_with("//") {
        let comment_content = &trimmed[2..].trim();
        
        // 检测装饰性注释（连续的特殊字符）
        let special_char_count = comment_content.chars()
            .filter(|c| "=-*_#│┌┐└┘├┤┬┴┼▲▼◄►".contains(*c))
            .count();
        
        if special_char_count > comment_content.len() / 2 {
            return String::new(); // 删除装饰性注释
        }
        
        // 🔥 改进：删除空注释行
        if comment_content.is_empty() {
            return String::new();
        }
        
        // 🔥 改进：删除 PACKING RULES 等大段说明注释
        if comment_content.to_uppercase().contains("PACKING RULES") ||
           comment_content.to_uppercase().contains("FROM THE LSB") ||
           comment_content.to_uppercase().contains("ZERO-BITS") {
            return String::new();
        }
    }
    
    // 4. 保留函数体内的逻辑注释（可能是漏洞逻辑解释）
    if in_function_body && trimmed.starts_with("//") {
        // 🔥 规则3：函数体内的单行注释可能解释漏洞逻辑，保留
        // 但仍然删除装饰性注释
        let comment_content = &trimmed[2..].trim();
        let special_char_count = comment_content.chars()
            .filter(|c| "=-*_#".contains(*c))
            .count();
        
        if special_char_count <= comment_content.len() / 3 {
            // 不是装饰性注释，保留
            return line.to_string();
        }
    }
    
    // 行内注释处理：如果行内既有代码又有注释
    if line.contains("//") && !line.trim().starts_with("//") {
        if in_function_body {
            // 函数体内：保留代码和注释（可能是重要说明）
            return line.to_string();
        } else {
            // 函数体外：只保留代码部分
            if let Some(idx) = line.find("//") {
                return line[..idx].to_string();
            }
        }
    }
    
    line.to_string()
}

// 🔥 库辅助函数黑名单（对漏洞分析无用的通用工具函数）
fn is_library_helper_function(func_name: &str) -> bool {
    const HELPER_BLACKLIST: &[&str] = &[
        // Address 库辅助函数
        "functionCall", "functionCallWithValue", "functionStaticCall",
        "functionDelegateCall", "verifyCallResult", "verifyCallResultFromTarget",
        "sendValue", "isContract", "_revert",
        
        // SafeMath 等数学库基础函数
        "tryAdd", "trySub", "tryMul", "tryDiv", "tryMod",
        "add", "sub", "mul", "div", "mod",
        
        // String 库函数
        "toString", "toHexString", "equal",
        
        // Arrays 库函数  
        "findUpperBound", "unsafeAccess",
        
        // 其他常见辅助函数
        "_msgSender", "_msgData", "_contextSuffixLength",
    ];
    
    HELPER_BLACKLIST.contains(&func_name)
}

// 🔥 标准库检测函数
fn is_standard_library_contract(contract_name: &str) -> bool {
    const STDLIB_CONTRACTS: &[&str] = &[
        // OpenZeppelin
        "Address", "SafeMath", "Math", "SignedMath", "Strings", "Arrays",
        "ECDSA", "ERC165", "ERC20", "ERC721", "ERC1155", "Ownable",
        "ReentrancyGuard", "Pausable", "AccessControl",
        
        // Forge Standard Library
        "Test", "Script", "Vm", "VmSafe", "console", "safeconsole",
        "StdAssertions", "StdCheats", "StdUtils", "StdInvariant",
        "StdError", "StdStorage", "StdStyle", "StdMath", "StdJson",
        "CommonBase", "ScriptBase", "TestBase",
        
        // Solmate
        "ERC20Minimal", "ERC721Minimal", "Auth", "Owned", "WETH",
        "SafeTransferLib", "FixedPointMathLib", "MerkleProofLib",
        
        // Common utilities (not business logic)
        "Create2", "Clone", "Multicall", "TransientReentrancyGuard",
        "Clones", "Context", "Counters", "EnumerableSet", "EnumerableMap",
    ];
    
    // 精确匹配或前缀匹配
    STDLIB_CONTRACTS.iter().any(|&stdlib| {
        contract_name == stdlib || 
        contract_name.starts_with(&format!("{}_", stdlib)) // 处理 Math_0, Math_1 等
    })
}

// 🔥 改进：基于AST的合约名提取（用于文本重建时的格式保留）
// 注意：这里仍需文本解析是因为要保留原始代码格式（空格、注释等）
// 但验证逻辑已通过AST完成，这里只是格式化提取
fn extract_contract_name(line: &str) -> String {
    if let Some(start) = line.find("contract ") {
        let after_contract = &line[start + 9..];
        if let Some(end) = after_contract.find(|c: char| !c.is_alphanumeric() && c != '_') {
            return after_contract[..end].trim().to_string();
        } else {
            return after_contract.trim().to_string();
        }
    } else if let Some(start) = line.find("library ") {
        let after_library = &line[start + 8..];
        if let Some(end) = after_library.find(|c: char| !c.is_alphanumeric() && c != '_') {
            return after_library[..end].trim().to_string();
        } else {
            return after_library.trim().to_string();
        }
    }
    String::new()
}

// 🔥 改进：基于AST的类型名提取（用于文本重建时的格式保留）
// 注意：不包括 interface，因为接口会被单独过滤
fn extract_type_name(line: &str) -> String {
    let keywords = ["type ", "struct ", "enum "];
    for keyword in &keywords {
        if let Some(start) = line.find(keyword) {
            let after_keyword = &line[start + keyword.len()..];
            if let Some(end) = after_keyword.find(|c: char| !c.is_alphanumeric() && c != '_') {
                return after_keyword[..end].trim().to_string();
            } else {
                return after_keyword.trim().to_string();
            }
        }
    }
    String::new()
}

// 辅助函数：提取完整的定义
fn extract_entire_definition(lines: &[&str], start_line: usize) -> String {
    let mut definition_lines = Vec::new();
    let mut brace_count: i32 = 0;
    let mut i = start_line;

    while i < lines.len() {
        let line = lines[i];
        definition_lines.push(line.to_string());

        brace_count += line.chars().filter(|&c| c == '{').count() as i32;
        let close_count = line.chars().filter(|&c| c == '}').count() as i32;
        if brace_count >= close_count {
            brace_count -= close_count;
        } else {
            brace_count = 0;
        }

        if brace_count == 0 && line.contains('}') {
            break;
        }
        i += 1;
    }

    definition_lines.join("\n")
}

// 🔥 新增：增强版函数提取 - 基于AST分析过滤接口函数和孤立注释
fn extract_contract_with_functions_filtered(
    lines: &[&str], 
    start_line: usize, 
    relevant_functions: &std::collections::HashSet<String>,
    function_levels: &std::collections::HashMap<String, usize>,
    max_level: usize,
) -> String {
    let mut result_lines = Vec::new();
    let mut i = start_line;
    let mut contract_brace_count = 0;
    let mut found_opening_brace = false;

    // 首先添加合约声明（直到第一个 {）
    while i < lines.len() {
        let line = lines[i];
        result_lines.push(line.to_string());
        
        if line.contains('{') {
            contract_brace_count = 1;
            found_opening_brace = true;
            i += 1;
            break;
        }
        i += 1;
    }

    if !found_opening_brace {
        return lines[start_line].to_string();
    }

    // 解析合约体
    while i < lines.len() && contract_brace_count > 0 {
        let line = lines[i];
        let trimmed = line.trim();

        // 检查是否是函数定义
        if is_function_start(trimmed) {
            let func_name = extract_function_name_from_line(trimmed);
            
            // 🔥 规则：过滤库辅助函数黑名单（这些对漏洞分析无用）
            if is_library_helper_function(&func_name) {
                i = skip_function_body(lines, i);
                continue;
            }
            
            // 🔥 函数级过滤：检查函数是否在relevant_functions中，并且层级在阈值内
            let is_in_relevant = !func_name.is_empty() && relevant_functions.contains(&func_name);
            let is_in_level = function_levels.get(&func_name).map_or(false, |&level| level <= max_level);
            
            let should_include = is_in_relevant || is_in_level;
            
            if should_include {
                // 提取整个函数
                let function_code = extract_function_at_position(lines, i);
                result_lines.push(function_code);
                
                // 跳过函数体
                i = skip_function_body(lines, i);
            } else {
                // 跳过不相关的函数
                i = skip_function_body(lines, i);
            }
        } else if is_state_variable_or_other(trimmed) {
            // 保留状态变量、事件、modifier、构造函数等
            if trimmed.starts_with("constructor") || 
               trimmed.starts_with("event ") || 
               trimmed.starts_with("modifier ") ||
               trimmed.starts_with("error ") ||
               is_state_variable_declaration(trimmed) {
                
                if trimmed.contains(';') {
                    // 单行声明
                    result_lines.push(line.to_string());
                } else {
                    // 多行声明（如 constructor 或 modifier）
                    let block_code = extract_block_at_position(lines, i);
                    result_lines.push(block_code);
                    i = skip_block(lines, i);
                }
            }
        } else {
            // 🔥 过滤孤立注释：只有紧邻函数/声明的注释才保留
            if trimmed.starts_with("//") || trimmed.starts_with("/*") {
                // 检查下一个非空行是否是相关内容
                if i + 1 < lines.len() {
                    let next_non_empty = find_next_non_empty_line(lines, i + 1);
                    if next_non_empty < lines.len() {
                        let next_trimmed = lines[next_non_empty].trim();
                        if is_function_start(next_trimmed) || next_trimmed.starts_with("constructor") || 
                           next_trimmed.starts_with("modifier") || is_state_variable_declaration(next_trimmed) {
                            result_lines.push(line.to_string());
                        }
                        // 否则跳过孤立的注释
                    }
                }
            } else if trimmed.is_empty() || trimmed == "}" {
                result_lines.push(line.to_string());
            }
        }

        // 更新括号计数
        contract_brace_count += line.chars().filter(|&c| c == '{').count() as i32;
        contract_brace_count -= line.chars().filter(|&c| c == '}').count() as i32;
        
        if contract_brace_count <= 0 {
            break;
        }
        
        i += 1;
    }

    result_lines.join("\n")
}

// 🔥 辅助函数：找到下一个非空行（用于孤立注释过滤）
fn find_next_non_empty_line(lines: &[&str], start: usize) -> usize {
    for i in start..lines.len().min(start + 5) {
        if !lines[i].trim().is_empty() {
            return i;
        }
    }
    lines.len()
}

// 辅助函数：提取合约，但只包含相关的函数
fn extract_contract_with_functions(lines: &[&str], start_line: usize, relevant_functions: &std::collections::HashSet<String>) -> String {
    let mut result_lines = Vec::new();
    let mut i = start_line;
    let mut contract_brace_count = 0;
    let mut found_opening_brace = false;

    // 首先添加合约声明（直到第一个 {）
    while i < lines.len() {
        let line = lines[i];
        result_lines.push(line.to_string());
        
        if line.contains('{') {
            contract_brace_count = 1;
            found_opening_brace = true;
            i += 1;
            break;
        }
        i += 1;
    }

    if !found_opening_brace {
        return lines[start_line].to_string();
    }

    // 解析合约体
    while i < lines.len() && contract_brace_count > 0 {
        let line = lines[i];
        let trimmed = line.trim();

        // 检查是否是函数定义
        if is_function_start(trimmed) {
            let func_name = extract_function_name_from_line(trimmed);
            
            // 只有相关的函数才包含
            if !func_name.is_empty() && relevant_functions.contains(&func_name) {
                // 提取整个函数
                let function_code = extract_function_at_position(lines, i);
                result_lines.push(function_code);
                
                // 跳过函数体
                i = skip_function_body(lines, i);
            } else {
                // 跳过不相关的函数
                i = skip_function_body(lines, i);
            }
        } else if is_state_variable_or_other(trimmed) {
            // 保留状态变量、事件、modifier、构造函数等
            if trimmed.starts_with("constructor") || 
               trimmed.starts_with("event ") || 
               trimmed.starts_with("modifier ") ||
               trimmed.starts_with("error ") ||
               is_state_variable_declaration(trimmed) {
                
                if trimmed.contains(';') {
                    // 单行声明
                    result_lines.push(line.to_string());
                } else {
                    // 多行声明（如 constructor 或 modifier）
                    let block_code = extract_block_at_position(lines, i);
                    result_lines.push(block_code);
                    i = skip_block(lines, i);
                }
            }
        } else {
            // 其他行（注释、空行等）可以选择性保留
            if trimmed.starts_with("//") || trimmed.is_empty() || trimmed == "}" {
                result_lines.push(line.to_string());
            }
        }

        // 更新括号计数
        contract_brace_count += line.chars().filter(|&c| c == '{').count() as i32;
        contract_brace_count -= line.chars().filter(|&c| c == '}').count() as i32;
        
        if contract_brace_count <= 0 {
            break;
        }
        
        i += 1;
    }

    result_lines.join("\n")
}

// 🔥 改进：基于AST验证的函数开始判断
// PDG分析已经识别了所有函数，这里只是文本匹配辅助
fn is_function_start(line: &str) -> bool {
    line.starts_with("function ") && !line.contains(';')
}

// 🔥 改进：函数名提取（配合AST验证）
// relevant_functions来自AST，这里提取是为了匹配验证
fn extract_function_name_from_line(line: &str) -> String {
    if let Some(start) = line.find("function ") {
        let after_function = &line[start + 9..];
        if let Some(end) = after_function.find('(') {
            return after_function[..end].trim().to_string();
        }
    }
    String::new()
}

// 辅助函数：提取函数代码
fn extract_function_at_position(lines: &[&str], start: usize) -> String {
    let mut func_lines = Vec::new();
    let mut brace_count = 0;
    let mut i = start;
    let mut found_opening = false;

    while i < lines.len() {
        let line = lines[i];
        func_lines.push(line.to_string());

        for ch in line.chars() {
            if ch == '{' {
                brace_count += 1;
                found_opening = true;
            } else if ch == '}' {
                brace_count -= 1;
            }
        }

        if found_opening && brace_count == 0 {
            break;
        }
        i += 1;
    }

    func_lines.join("\n")
}

// 辅助函数：跳过函数体
fn skip_function_body(lines: &[&str], start: usize) -> usize {
    let mut brace_count = 0;
    let mut i = start;
    let mut found_opening = false;

    while i < lines.len() {
        let line = lines[i];

        for ch in line.chars() {
            if ch == '{' {
                brace_count += 1;
                found_opening = true;
            } else if ch == '}' {
                brace_count -= 1;
            }
        }

        if found_opening && brace_count == 0 {
            return i + 1;
        }
        i += 1;
    }

    i
}

// 辅助函数：提取代码块
fn extract_block_at_position(lines: &[&str], start: usize) -> String {
    extract_function_at_position(lines, start)
}

// 辅助函数：跳过代码块
fn skip_block(lines: &[&str], start: usize) -> usize {
    skip_function_body(lines, start)
}

// 辅助函数：判断是否是状态变量或其他声明
fn is_state_variable_or_other(line: &str) -> bool {
    !line.starts_with("function ") && !line.is_empty() && !line.starts_with("//")
}

// 辅助函数：判断是否是状态变量声明
fn is_state_variable_declaration(line: &str) -> bool {
    // 简化判断：包含类型关键字
    let keywords = ["uint", "int", "bool", "address", "bytes", "string", "mapping"];
    keywords.iter().any(|&kw| line.contains(kw)) && !line.starts_with("function")
}

/// 三层过滤结果
struct ThreeLayerFilterResult {
    blacklist: std::collections::HashSet<String>,  // 第一层：静态黑名单（直接剔除）
    whitelist: std::collections::HashSet<String>,  // 第二层：S1.2保护白名单（强制保留）
    graylist: std::collections::HashSet<String>,   // 第三层：语义灰名单（待LLM仲裁）
}

/// 第一层：静态黑名单过滤（Rust正则 - 绝对噪音）
/// 直接剔除：std*, console, Vm, IMulticall3 等标准库
fn apply_static_blacklist(contract: &str) -> bool {
    use regex::Regex;
    
    let blacklist_patterns = vec![
        Regex::new(r"^std").unwrap(),             // std*, stdMath, stdStorage等
        Regex::new(r"^Std").unwrap(),             // Std*, StdStyle, StdConstants等
        Regex::new(r"console").unwrap(),          // console, safeconsole
        Regex::new(r"^Math_\d+$").unwrap(),       // Math_0, Math_1, Math_2等
        Regex::new(r"^Strings_\d+$").unwrap(),    // Strings_0, Strings_1等
        Regex::new(r"^Vm$").unwrap(),             // Foundry VM
        Regex::new(r"^Script$").unwrap(),         // Foundry Script
        Regex::new(r"^IMulticall").unwrap(),      // IMulticall3等接口
    ];
    
    blacklist_patterns.iter().any(|re| re.is_match(contract))
}

/// 第二层：S1.2保护白名单（强制保留 - 防止LLM误删）
/// 保留：*Mock*, *Test*, PoC, *Setup* 等PoC环境关键合约
fn apply_s12_whitelist(contract: &str, variable_name: &str) -> bool {
    let must_keep_patterns = [
        "Mock",     // Mock合约：S1.2需要验证环境设置
        "Test",     // 测试合约：PoC的核心逻辑
        "PoC",      // PoC合约本身
        "Setup",    // 环境设置合约
    ];
    
    // 规则1: 包含目标变量名 → 强制保留
    if contract.to_lowercase().contains(&variable_name.to_lowercase()) {
        return true;
    }
    
    // 规则2: 匹配S1.2关键模式 → 强制保留
    must_keep_patterns.iter().any(|p| contract.contains(p))
}

/// 三层漏斗过滤：黑名单 → 白名单 → 灰名单
fn three_layer_filter(
    contracts: &std::collections::HashSet<String>, 
    variable_name: &str,
) -> ThreeLayerFilterResult {
    let mut result = ThreeLayerFilterResult {
        blacklist: std::collections::HashSet::new(),
        whitelist: std::collections::HashSet::new(),
        graylist: std::collections::HashSet::new(),
    };
    
    println!("\n🔄 Applying Three-Layer Funnel Filter...\n");
    
    for contract in contracts {
        // 第一层：静态黑名单检查
        if apply_static_blacklist(contract) {
            println!("🚫 Layer 1 Blacklist: {} (static noise)", contract);
            result.blacklist.insert(contract.clone());
            continue;
        }
        
        // 第二层：S1.2保护白名单检查
        if apply_s12_whitelist(contract, variable_name) {
            println!("✅ Layer 2 Whitelist: {} (S1.2 protected)", contract);
            result.whitelist.insert(contract.clone());
            continue;
        }
        
        // 第三层：语义灰名单（待LLM仲裁）
        println!("⚠️  Layer 3 Graylist: {} (pending LLM arbitration)", contract);
        result.graylist.insert(contract.clone());
    }
    
    println!("\n📊 Three-Layer Filter Summary:");
    println!("   Total contracts: {}", contracts.len());
    println!("   🚫 Blacklist (filtered): {}", result.blacklist.len());
    println!("   ✅ Whitelist (kept): {}", result.whitelist.len());
    println!("   ⚠️  Graylist (pending LLM): {}\n", result.graylist.len());
    
    result
}

/// LLM仲裁：判断灰名单合约是"通用库"还是"业务逻辑"
async fn llm_arbitrate_graylist(
    graylist: &std::collections::HashSet<String>,
    api_key: &str,
    base_url: &str,
    model: &str,
) -> Result<std::collections::HashSet<String>, Box<dyn std::error::Error>> {
    if graylist.is_empty() {
        return Ok(std::collections::HashSet::new());
    }
    
    println!("🤖 Asking LLM to arbitrate {} graylist contracts...", graylist.len());
    
    let contract_list = graylist.iter()
        .enumerate()
        .map(|(i, c)| format!("[{}] {}", i + 1, c))
        .collect::<Vec<_>>()
        .join("\n");
    
    let system_prompt = r#"You are a Solidity security expert analyzing PoC (Proof-of-Concept) code.

Your task: Classify contracts as either "Generic Library" or "Business Logic".

Classification Rules:
1. **Generic Library** (should be FILTERED to save context):
   - Pure math utilities (FixedPointMath, SafeCast, SignedMath, FullMath)
   - Token standard helpers (ERC20, ERC721 base implementations)
   - Common data structures (EnumerableSet, BitMaps)
   - General-purpose utilities (Clone, Errors, Constants)
   - OpenZeppelin/Solady standard libraries

2. **Business Logic** (should be KEPT for PoC analysis):
   - Protocol-specific contracts (Vault, Pool, Manager, Accountant)
   - Custom financial logic (PanopticMath, CollateralTracker)
   - Integration adapters (specific to the protocol)
   - State management contracts

Output Format (VALID JSON ONLY):
{
  "keep": [<list of contract names to KEEP>],
  "filter": [<list of contract names to FILTER>],
  "reasoning": "<brief explanation>"
}

Example:
{
  "keep": ["PanopticVaultAccountant", "CollateralTracker"],
  "filter": ["FixedPointMathLib", "SafeCast", "FullMath"],
  "reasoning": "Math libs are generic; Vault/Tracker are protocol-specific"
}"#;

    let user_prompt = format!(
        "Classify these contracts:\n\n{}\n\nReturn JSON with 'keep' and 'filter' arrays.",
        contract_list
    );
    
    let client = reqwest::Client::new();
    let request_body = serde_json::json!({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 4000
    });
    
    let response = client
        .post(format!("{}/chat/completions", base_url))
        .header("Authorization", format!("Bearer {}", api_key))
        .json(&request_body)
        .timeout(std::time::Duration::from_secs(60))
        .send()
        .await?;
    
    let response_text = response.text().await?;
    
    // 解析LLM响应
    let parsed: serde_json::Value = serde_json::from_str(&response_text)
        .map_err(|e| format!("Failed to parse LLM response: {}", e))?;
    
    let content = parsed["choices"][0]["message"]["content"]
        .as_str()
        .ok_or("No content in LLM response")?;
    
    // 提取JSON
    let json_start = content.find('{').ok_or("No JSON found in response")?;
    let json_end = content.rfind('}').ok_or("No JSON end found")?;
    let json_str = &content[json_start..=json_end];
    
    let decision: serde_json::Value = serde_json::from_str(json_str)?;
    
    let mut keep_set = std::collections::HashSet::new();
    if let Some(keep_array) = decision["keep"].as_array() {
        for item in keep_array {
            if let Some(name) = item.as_str() {
                keep_set.insert(name.to_string());
            }
        }
    }
    
    println!("🤖 LLM Decision:");
    println!("   ✅ Keep: {} contracts", keep_set.len());
    println!("   🗑️  Filter: {} contracts", graylist.len() - keep_set.len());
    if let Some(reasoning) = decision["reasoning"].as_str() {
        println!("   💡 Reasoning: {}\n", reasoning);
    }
    
    Ok(keep_set)
}

// 🔥 从静态切片结果中提取合约和函数信息
// 注意：这里的文本解析是必要的，因为：
// 1. 输入是analyzer::get_source_slice的字符串输出（已经是文本格式）
// 2. 这是two-phase处理的Phase 1，用于快速过滤，避免LLM分析所有代码
// 3. 真正的AST验证在Phase 2（get_source_from_nodes）中完成
fn extract_contracts_and_functions(slice: &[String]) -> (std::collections::HashSet<String>, std::collections::HashSet<String>) {
    let mut contracts = std::collections::HashSet::new();
    let mut functions = std::collections::HashSet::new();
    
    for code_block in slice {
        for line in code_block.lines() {
            let trimmed = line.trim();
            
            // 提取合约名（文本匹配，Phase 2会用AST验证）
            if trimmed.starts_with("contract ") || trimmed.starts_with("library ") {
                let name = extract_contract_name(trimmed);
                if !name.is_empty() {
                    contracts.insert(name);
                }
            }
            
            // 提取函数名（文本匹配，Phase 2会用AST验证）
            if trimmed.starts_with("function ") {
                let name = extract_function_name_from_line(trimmed);
                if !name.is_empty() {
                    functions.insert(name);
                }
            }
        }
    }
    
    (contracts, functions)
}

// 🔥 改进：构建函数层级关系（以函数为最小粒度）
// 返回：HashMap<函数名, 层级> - 层级越小越重要（0=目标函数，1=直接调用，2=间接调用...）
// 同时返回：HashMap<合约名, 层级> - 合约层级取其所有函数的最小层级
fn build_function_level_hierarchy(
    analysis: &AnalysisResult,
    relevant_functions: &std::collections::HashSet<String>,
) -> (std::collections::HashMap<String, usize>, std::collections::HashMap<String, usize>) {
    use std::collections::{HashMap, HashSet, VecDeque};
    
    let mut function_levels = HashMap::new();
    let mut contract_levels = HashMap::new();
    let mut queue = VecDeque::new();
    let mut visited = HashSet::new();
    
    // 🔥 将relevant_functions中的所有函数设为0级（这些是PDG切片的结果）
    for func in relevant_functions {
        function_levels.insert(func.clone(), 0);
        queue.push_back((func.clone(), 0));
        visited.insert(func.clone());
    }
    
    // 🔥 BFS遍历函数调用关系（向被调用方向扩展 - 找当前函数调用了哪些函数）
    while let Some((current_func, current_level)) = queue.pop_front() {
        // 查找当前函数调用的其他函数（被调用者）
        let called_functions = find_called_functions(analysis, &current_func);
        
        for called_func in called_functions {
            if !visited.contains(&called_func) {
                visited.insert(called_func.clone());
                function_levels.insert(called_func.clone(), current_level + 1);
                queue.push_back((called_func, current_level + 1));
            }
        }
    }
    
    // 🔥 从函数层级推导合约层级（合约的层级 = 其所有函数的最小层级）
    for (contract_name, functions) in &analysis.contract_registry.function_map {
        let mut min_level = usize::MAX;
        for func_name in functions.keys() {
            if let Some(&level) = function_levels.get(func_name) {
                min_level = min_level.min(level);
            }
        }
        if min_level != usize::MAX {
            contract_levels.insert(contract_name.clone(), min_level);
        }
    }
    
    (function_levels, contract_levels)
}

// 🔥 改进：基于AST分析函数调用关系（不依赖PDG Call edges）
// 通过分析函数的label字段来提取被调用的函数名
// 注意：这里使用字符串解析是因为PDG不track内部函数调用的Call边
fn find_called_functions(
    analysis: &AnalysisResult,
    function_name: &str,
) -> Vec<String> {
    let mut called_functions: std::collections::HashSet<String> = std::collections::HashSet::new();
    
    // 第一步：找到当前函数的所有节点
    let mut function_nodes = std::collections::HashSet::new();
    for (node_id, node) in &analysis.program_dependency_graph.nodes {
        if let Some(func_context) = &node.function_context {
            if func_context == function_name {
                function_nodes.insert(*node_id);
            }
        }
    }
    
    // 第二步：从节点label中提取函数调用（AST级别）
    // PDG label格式: "call Expr { span: ..., kind: Ident(functionName) }"
    for node_id in &function_nodes {
        if let Some(node) = analysis.program_dependency_graph.nodes.get(node_id) {
            let label = &node.label;
            
            // Case 1: ExternalCall nodes (跨合约调用)
            if matches!(node.kind, crate::analyzer::NodeKind::ExternalCall) {
                 let called_name = if let Some(idx) = label.rfind('.') {
                     &label[idx + 1..]
                 } else {
                     label.as_str()
                 };
                 
                 // Check if this name corresponds to a known function
                 let is_known = analysis.contract_registry.function_map.values()
                     .any(|funcs| funcs.contains_key(called_name));
                     
                 if is_known {
                     if !is_interface_function(analysis, called_name) && called_name != function_name {
                         called_functions.insert(called_name.to_string());
                     }
                 }
            }

            // Case 2: Internal calls (AST pattern matching)
            // 检查所有已知函数名
            for (func_name, _) in analysis.contract_registry.function_map.iter()
                .flat_map(|(_, funcs)| funcs.iter()) {
                // 🔥 匹配PDG label中的函数调用模式:
                // 1. "kind: Ident(functionName)" - AST表达式调用
                // 2. "functionName(" - 简单函数调用
                let ident_pattern = format!("Ident({})", func_name);
                let call_pattern = format!("{}(", func_name);
                
                if label.contains(&ident_pattern) || label.contains(&call_pattern) {
                    // 🔥 过滤接口函数和自身
                    if !is_interface_function(analysis, func_name) && func_name.as_str() != function_name {
                        called_functions.insert(func_name.to_string());
                    }
                }
            }
        }
    }
    
    called_functions.into_iter().collect()
}

// 🔥 改进：基于PDG节点判断函数是否为接口函数（只有声明，无实现）
// 如果函数在PDG中有节点，说明有实现；否则只是接口声明
fn is_interface_function(analysis: &AnalysisResult, function_name: &str) -> bool {
    // 检查函数是否有PDG节点（有节点=有实现，无节点=接口函数）
    for node in analysis.program_dependency_graph.nodes.values() {
        if let Some(func_context) = &node.function_context {
            if func_context == function_name {
                // 找到节点，说明有实现
                return false;
            }
        }
    }
    
    // 没有找到任何PDG节点
    // 🔥 但这不一定是接口函数！可能是two-phase模式下phase 1没有包含的函数
    // 解决方案：检查ContractRegistry - 只要在Registry中有entry_id，就说明有实现
    for functions in analysis.contract_registry.function_map.values() {
        if functions.contains_key(function_name) {
            // 在ContractRegistry中找到，说明有实现，不是接口函数
            return false;
        }
    }
    
    // 既不在PDG也不在ContractRegistry，确实是接口函数
    true
}

// 🔥 改进：基于PDG edges的调用关系分析（完全消除字符串匹配）
// 通过分析Call类型的边，直接追踪函数间的调用关系
fn find_called_contracts(
    analysis: &AnalysisResult,
    contract_name: &str,
    relevant_contracts: &std::collections::HashSet<String>,
    relevant_functions: &std::collections::HashSet<String>,
) -> Vec<String> {
    let mut called = std::collections::HashSet::new();
    
    // 🔥 策略改进：通过PDG的Call边追踪调用
    // 1. 找到属于当前合约的所有函数节点
    // 2. 查找这些节点的出边（outgoing edges）
    // 3. 如果边的类型是Call，找到目标节点
    // 4. 从目标节点的function_context反查合约（ContractRegistry）
    
    // 第一步：收集当前合约的所有函数节点ID
    let mut contract_function_nodes = std::collections::HashSet::new();
    for (node_id, node) in &analysis.program_dependency_graph.nodes {
        if let Some(func_context) = &node.function_context {
            if relevant_functions.contains(func_context) {
                // 验证函数属于目标合约
                if let Some(node_contract) = find_contract_for_function(analysis, func_context) {
                    if node_contract == contract_name {
                        contract_function_nodes.insert(*node_id);
                    }
                }
            }
        }
    }
    
    // 第二步：遍历PDG edges，找到Call类型的边
    for edge in &analysis.program_dependency_graph.edges {
        // 检查是否是从当前合约发出的调用
        if !contract_function_nodes.contains(&edge.from) {
            continue;
        }
        
        // 只处理Call类型的边（精确的调用关系）
        if !matches!(edge.kind, crate::analyzer::EdgeKind::Call) {
            continue;
        }
        
        // 找到被调用的目标节点
        if let Some(target_node) = analysis.program_dependency_graph.nodes.get(&edge.to) {
            // 从目标节点的function_context获取被调用的函数
            if let Some(called_func) = &target_node.function_context {
                // 🔥 关键改进：通过ContractRegistry（AST）查找函数所属合约
                // 完全避免了label字符串匹配
                if let Some(target_contract) = find_contract_for_function(analysis, called_func) {
                    // 只关注relevant_contracts中的合约（跨合约调用）
                    if relevant_contracts.contains(&target_contract) && target_contract != contract_name {
                        called.insert(target_contract);
                    }
                }
            }
        }
    }
    
    called.into_iter().collect()
}

// 🔥 基于AST的ContractRegistry查找函数所属合约
fn find_contract_for_function(analysis: &AnalysisResult, function_name: &str) -> Option<String> {
    for (contract_name, functions) in &analysis.contract_registry.function_map {
        if functions.contains_key(function_name) {
            return Some(contract_name.clone());
        }
    }
    None
}

// 辅助函数：从调用信息中提取目标合约
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