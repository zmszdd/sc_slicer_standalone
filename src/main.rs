#![allow(unused)]
//!
//! SC Slicer - Solidity 代码切片工具
//!
//! 命令行入口程序，负责解析用户参数、调用代码分析器
//! 和语义切片器，对 Solidity 智能合约进行安全分析
//! 和代码切片。
//!
//! ## 架构设计：AST 分析 + Span 精确提取
//!
//! ### 核心原则：
//! - **决策层（AST）**：使用AST/PDG分析结果来判断语义相关性
//! - **提取层（AST Span）**：使用 solar-parser 的 byte span 提取完整 AST 节点
//!
//! ### 为什么使用 Span 提取？
//! AST 节点提供准确的语法边界，Span 又能保留原始格式：
//! - 不需要正则识别函数或变量
//! - 不需要手写大括号计数
//! - 不会被字符串、注释或单行类型定义中的符号干扰
//!
//! ### 分层架构：
//! 1. **AST分析层**：
//!    - `ContractRegistry`: 合约→函数映射（来自AST）
//!    - `PDG`: 数据流和控制流分析（来自AST）
//!    - `relevant_functions`: 通过PDG切片得到（基于AST）
//!
//! 2. **AST Span 提取层**：
//!    - `AstSliceIndex`: 在 Arena 生命周期内记录合约、函数、变量和类型节点
//!    - `AstSliceIndex::render()`: 只输出相关 AST 节点的原始源码片段
//!

use clap::{Arg, Command};
use std::ffi::OsStr;
use std::fs;
use std::fs::OpenOptions;
use std::io::Write;
use std::path::{Path, PathBuf};

mod analyzer;
mod execution_log;
pub mod noise_reduction;
pub mod semantic_slicer;
mod source_normalizer;
pub mod sol_resurrect_v2;

use crate::analyzer::AnalysisResult;
use crate::noise_reduction::NoiseReductionPipeline;
use crate::semantic_slicer::SemanticGraphAdapter;
use petgraph::Direction;
use solar_ast::{self as ast, FunctionKind, ItemKind, SourceUnit};
use solar_interface::{SourceMap, Span};
use std::collections::{HashMap, HashSet};

struct PdgAdapter<'a> {
    analysis: &'a AnalysisResult,
    source_code: &'a str,
}

#[derive(Debug, Clone)]
struct TargetSpec {
    contract: String,
    entry_function: String,
    focus_symbol: String,
}

#[derive(Debug, Clone)]
struct HarnessPolicy {
    include_setup: bool,
    include_same_contract_helpers: bool,
    include_inherited_helpers: bool,
    allow_text_dependency_expansion: bool,
    max_harness_functions: usize,
}

impl Default for HarnessPolicy {
    fn default() -> Self {
        Self {
            include_setup: true,
            include_same_contract_helpers: true,
            include_inherited_helpers: true,
            allow_text_dependency_expansion: false,
            max_harness_functions: 96,
        }
    }
}

impl<'a> SemanticGraphAdapter for PdgAdapter<'a> {
    fn get_predecessors(&self, node_id: usize) -> Vec<usize> {
        self.analysis
            .program_dependency_graph
            .graph
            .neighbors_directed(
                petgraph::graph::NodeIndex::new(node_id),
                Direction::Incoming,
            )
            .map(|n| n.index())
            .collect()
    }

    fn get_node_source(&self, node_id: usize) -> String {
        if let Some(&stored_node_id) = self
            .analysis
            .program_dependency_graph
            .graph
            .node_weight(petgraph::graph::NodeIndex::new(node_id))
        {
            if let Some(node) = self
                .analysis
                .program_dependency_graph
                .nodes
                .get(&stored_node_id)
            {
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
        if let Some(&stored_node_id) = self
            .analysis
            .program_dependency_graph
            .graph
            .node_weight(petgraph::graph::NodeIndex::new(node_id))
        {
            if let Some(node) = self
                .analysis
                .program_dependency_graph
                .nodes
                .get(&stored_node_id)
            {
                matches!(node.kind, crate::analyzer::NodeKind::ControlCondition)
            } else {
                false
            }
        } else {
            false
        }
    }

    fn get_node_info(&self, node_id: usize) -> Option<&analyzer::PdgNode> {
        if let Some(&stored_node_id) = self
            .analysis
            .program_dependency_graph
            .graph
            .node_weight(petgraph::graph::NodeIndex::new(node_id))
        {
            self.analysis
                .program_dependency_graph
                .nodes
                .get(&stored_node_id)
        } else {
            None
        }
    }

    fn is_keyword(&self, token: &str) -> bool {
        // Solidity 关键字列表
        matches!(
            token,
            "function"
                | "if"
                | "else"
                | "for"
                | "while"
                | "return"
                | "uint256"
                | "address"
                | "bool"
                | "string"
                | "bytes"
                | "require"
                | "emit"
                | "event"
                | "contract"
                | "pragma"
                | "import"
                | "public"
                | "private"
                | "internal"
                | "external"
                | "view"
                | "pure"
                | "payable"
                | "constructor"
                | "modifier"
                | "struct"
                | "enum"
                | "mapping"
                | "memory"
                | "storage"
                | "calldata"
        )
    }

    fn extract_identifiers(&self, node_id: usize) -> Vec<String> {
        // 简化实现：从源码中提取标识符
        let code = self.get_node_source(node_id);
        let mut ids = Vec::new();
        for word in code.split(|c: char| !c.is_alphanumeric() && c != '_') {
            if !word.is_empty()
                && word.chars().next().unwrap().is_alphabetic()
                && !self.is_keyword(word)
            {
                ids.push(word.to_string());
            }
        }
        ids
    }

    fn get_contract_context_summary(&self) -> String {
        let mut context_parts = Vec::new();

        for line in self.source_code.lines() {
            let trimmed = line.trim();
            if trimmed.starts_with("pragma ")
                || trimmed.starts_with("import ")
                || trimmed.starts_with("contract ")
                || trimmed.starts_with("library ")
                || trimmed.starts_with("interface ")
            {
                context_parts.push(line.to_string());
            }
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
            let is_function_call =
                matches!(node.kind, NodeKind::FunctionCall | NodeKind::ExternalCall);

            if !is_function_call {
                continue;
            }

            // 提取调用方函数名
            let caller = node
                .function_context
                .clone()
                .unwrap_or_else(|| "global".to_string());

            // 从label中提取被调用方函数名
            let callee = self.extract_callee_name(&node.label);

            // 获取调用处源代码
            let code_line = self.get_node_source(node_id);

            // 检测返回值是否被使用（简化：检查是否有赋值符号）
            let return_var_used = code_line.contains('=') && !code_line.trim().starts_with("//");

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
        let external_set: std::collections::HashSet<String> =
            calls.iter().map(|c| c.code_snippet.clone()).collect();

        for cap in internal_pattern.captures_iter(code) {
            let callee = cap.get(1).unwrap().as_str().to_string();
            let full_match = cap.get(0).unwrap().as_str().to_string();

            // 过滤：关键字、已识别的外部调用、类型转换
            if !self.is_keyword(&callee)
                && !external_set.contains(&full_match)
                && !matches!(
                    callee.as_str(),
                    "uint256" | "address" | "bytes32" | "uint" | "int"
                )
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
        let pattern =
            Regex::new(r"vm\.store\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)").unwrap();

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
                if let Some(control_node) =
                    self.analysis.program_dependency_graph.nodes.get(&edge.from)
                {
                    let label_lower = control_node.label.to_lowercase();
                    if label_lower.contains("require")
                        || label_lower.contains("assert")
                        || label_lower.contains("if")
                    {
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
}

#[derive(Debug, Clone, PartialEq, Eq)]
enum AstContractItemKind {
    Function,
    Modifier,
    Variable,
    Struct,
    Enum,
    Udvt,
    Error,
    Event,
    Using,
}

#[derive(Debug, Clone)]
struct AstContractItem {
    kind: AstContractItemKind,
    name: Option<String>,
    type_name: Option<String>,
    type_refs: HashSet<String>,
    code: String,
}

#[derive(Debug, Clone)]
struct AstTopLevelItem {
    name: Option<String>,
    type_refs: HashSet<String>,
    code: String,
}

#[derive(Debug, Clone)]
struct AstContractSlice {
    name: String,
    kind: ast::ContractKind,
    signature: String,
    body_items: Vec<AstContractItem>,
}

#[derive(Debug, Default, Clone)]
struct AstSliceIndex {
    top_level_headers: Vec<String>,
    top_level_types: Vec<AstTopLevelItem>,
    contracts: Vec<AstContractSlice>,
    variable_types: HashMap<String, String>,
    using_libraries: HashSet<String>,
}

#[derive(Debug, Default, Clone)]
pub struct SliceSelection {
    pub relevant_contracts: HashSet<String>,
    pub full_contracts: HashSet<String>,
    pub relevant_functions: HashSet<String>,
    pub relevant_contract_functions: HashSet<String>,
    pub relevant_variables: HashSet<String>,
    pub function_levels: HashMap<String, usize>,
    pub contract_levels: HashMap<String, usize>,
    pub dependency_traces: HashMap<String, String>,
    pub target_contract: String,
    pub target_entry_function: String,
}

impl SliceSelection {
    pub fn contract_function_key(contract: &str, function: &str) -> String {
        format!("{}::{}", contract, function)
    }

    pub fn add_contract_function(&mut self, contract: &str, function: &str, reason: &str) -> bool {
        if contract.trim().is_empty() || function.trim().is_empty() {
            return false;
        }

        self.relevant_contracts.insert(contract.to_string());
        self.relevant_functions.insert(function.to_string());
        let key = Self::contract_function_key(contract, function);
        let inserted = self.relevant_contract_functions.insert(key.clone());
        self.dependency_traces
            .entry(key)
            .or_insert_with(|| reason.to_string());
        inserted
    }

    pub fn contains_contract_function(&self, contract: &str, function: &str) -> bool {
        self.relevant_contract_functions
            .contains(&Self::contract_function_key(contract, function))
    }

    pub fn has_target_entry(&self) -> bool {
        !self.target_contract.trim().is_empty() && !self.target_entry_function.trim().is_empty()
    }
}

impl AstSliceIndex {
    fn from_asts(asts: &[SourceUnit], source_map: &SourceMap) -> Self {
        let mut index = AstSliceIndex::default();

        for source_unit in asts {
            for item in source_unit.items.iter() {
                match &item.kind {
                    ItemKind::Pragma(_) | ItemKind::Import(_) | ItemKind::Using(_) => {
                        if let ItemKind::Using(using_directive) = &item.kind {
                            collect_using_libraries(using_directive, &mut index.using_libraries);
                        }
                        if let Some(code) = snippet_for_span(source_map, item.span) {
                            push_unique(&mut index.top_level_headers, code);
                        }
                    }
                    ItemKind::Struct(_)
                    | ItemKind::Enum(_)
                    | ItemKind::Udvt(_)
                    | ItemKind::Error(_)
                    | ItemKind::Event(_) => {
                        if let Some(top_level_item) = top_level_item_from_ast(source_map, item) {
                            push_unique_top_level(&mut index.top_level_types, top_level_item);
                        }
                    }
                    ItemKind::Contract(contract) => {
                        let signature = contract_signature_snippet(source_map, item, contract);
                        let mut body_items = Vec::new();

                        for body_item in contract.body.iter() {
                            if let ItemKind::Using(using_directive) = &body_item.kind {
                                collect_using_libraries(
                                    using_directive,
                                    &mut index.using_libraries,
                                );
                            }
                            if let Some(contract_item) =
                                contract_body_item_from_ast(source_map, body_item)
                            {
                                if let AstContractItemKind::Variable = contract_item.kind {
                                    if let (Some(var_name), Some(type_name)) =
                                        (&contract_item.name, &contract_item.type_name)
                                    {
                                        index
                                            .variable_types
                                            .insert(var_name.clone(), type_name.clone());
                                    }
                                }
                                body_items.push(contract_item);
                            }
                        }

                        index.contracts.push(AstContractSlice {
                            name: contract.name.to_string(),
                            kind: contract.kind,
                            signature,
                            body_items,
                        });
                    }
                    ItemKind::Function(_) | ItemKind::Variable(_) => {
                        if let Some(top_level_item) = top_level_item_from_ast(source_map, item) {
                            push_unique_top_level(&mut index.top_level_types, top_level_item);
                        }
                    }
                }
            }
        }

        index
    }

    fn contract_has_function(&self, contract_name: &str, function_name: &str) -> bool {
        self.contracts
            .iter()
            .find(|contract| contract.name == contract_name)
            .map(|contract| {
                contract.body_items.iter().any(|item| {
                    matches!(item.kind, AstContractItemKind::Function)
                        && item.name.as_deref() == Some(function_name)
                })
            })
            .unwrap_or(false)
    }

    fn base_contracts(&self, contract_name: &str) -> Vec<String> {
        let Some(contract) = self
            .contracts
            .iter()
            .find(|contract| contract.name == contract_name)
        else {
            return Vec::new();
        };

        parse_base_contracts_from_signature(&contract.signature)
            .into_iter()
            .filter(|base| self.contracts.iter().any(|contract| contract.name == *base))
            .collect()
    }

    fn render(
        &self,
        selection: &SliceSelection,
        include_types: bool,
        exclude_libs: bool,
        max_level: usize,
    ) -> Vec<String> {
        let mut output = Vec::new();

        for header in &self.top_level_headers {
            push_unique(&mut output, header.clone());
        }

        if include_types {
            for type_def in &self.top_level_types {
                push_unique(&mut output, type_def.code.clone());
            }
        }

        let mut emitted_defs = HashSet::new();
        let mut required_type_refs = HashSet::new();
        let mut required_base_refs = HashSet::new();

        if include_types {
            for type_def in &self.top_level_types {
                if let Some(name) = &type_def.name {
                    emitted_defs.insert(name.clone());
                }
                required_type_refs.extend(type_def.type_refs.iter().cloned());
            }
        }

        for contract in &self.contracts {
            let is_interface = matches!(contract.kind, ast::ContractKind::Interface);
            let is_selected = selection.relevant_contracts.contains(&contract.name)
                || selection
                    .contract_levels
                    .get(&contract.name)
                    .map_or(false, |level| *level <= max_level)
                || contract.body_items.iter().any(|item| {
                    matches!(item.kind, AstContractItemKind::Function)
                        && item.name.as_ref().map_or(false, |name| {
                            selection.contains_contract_function(&contract.name, name)
                        })
                        || item
                            .name
                            .as_ref()
                            .map_or(false, |name| selection.relevant_variables.contains(name))
                });

            if is_interface && !selection.relevant_contracts.contains(&contract.name) {
                continue;
            }

            if !is_selected {
                continue;
            }

            if exclude_libs && contract.kind == ast::ContractKind::Library {
                continue;
            }

            required_base_refs.extend(parse_base_contracts_from_signature(&contract.signature));

            if is_standard_library_contract(&contract.name) {
                // Most stdlib contracts get an empty stub.
                // But some (like Clone) provide inherited functions that child contracts need —
                // these must be emitted with their real body.
                if is_stdlib_needing_full_body(&contract.name) {
                    let mut rendered = String::new();
                    let signature = contract.signature.trim_end();
                    if signature.ends_with('{') {
                        rendered.push_str(signature);
                    } else {
                        rendered.push_str(signature);
                        rendered.push_str(" {");
                    }
                    for item in &contract.body_items {
                        rendered.push_str("\n");
                        rendered.push_str(indent_contract_item(&item.code).trim_end());
                        rendered.push_str("\n");
                    }
                    rendered.push_str("}");
                    push_unique(&mut output, rendered);
                } else {
                    push_unique(
                        &mut output,
                        format!("{} {} {{}}", contract.kind.to_str(), contract.name),
                    );
                }
                emitted_defs.insert(contract.name.clone());
                continue;
            }

            let mut rendered = String::new();
            let signature = contract.signature.trim_end();
            if signature.ends_with('{') {
                rendered.push_str(signature);
            } else if signature.trim_end().ends_with('}') {
                rendered.push_str(signature.trim_end_matches('}').trim_end());
                rendered.push_str(" {");
            } else {
                rendered.push_str(signature);
                rendered.push_str(" {");
            }

            for item in &contract.body_items {
                if should_exclude_harness_item(&contract.name, item, selection) {
                    continue;
                }

                if selection.full_contracts.contains(&contract.name)
                    || should_include_contract_item(&contract.name, item, selection, include_types)
                {
                    required_type_refs.extend(item.type_refs.iter().cloned());
                    rendered.push_str("\n");
                    rendered.push_str(indent_contract_item(&item.code).trim_end());
                    rendered.push_str("\n");
                }
            }

            rendered.push_str("}");
            emitted_defs.insert(contract.name.clone());
            push_unique(&mut output, rendered);
        }

        let mut missing_library_stubs = Vec::new();
        for library_name in &self.using_libraries {
            let has_library = self
                .contracts
                .iter()
                .any(|contract| contract.name == *library_name);
            let emitted_library = output.iter().any(|block| {
                block.starts_with(&format!("library {} ", library_name))
                    || block.starts_with(&format!("library {}{{", library_name))
                    || block.starts_with(&format!("library {} {{", library_name))
            });

            if !has_library || !emitted_library {
                push_unique(
                    &mut missing_library_stubs,
                    format!("library {} {{}}", library_name),
                );
            }
            emitted_defs.insert(library_name.clone());
        }
        insert_before_contract_blocks(&mut output, missing_library_stubs);

        let mut missing_base_stubs = Vec::new();
        for base_name in required_base_refs {
            if should_stub_type(&base_name, &emitted_defs) {
                push_unique(
                    &mut missing_base_stubs,
                    format!(
                        "abstract contract {} {{\n    modifier onlyOwner() virtual {{ _; }}\n}}",
                        base_name
                    ),
                );
                emitted_defs.insert(base_name);
            }
        }
        insert_before_contract_blocks(&mut output, missing_base_stubs);

        let mut missing_type_stubs = Vec::new();
        for type_name in required_type_refs {
            if should_stub_type(&type_name, &emitted_defs) {
                push_unique(
                    &mut missing_type_stubs,
                    format!("interface {} {{}}", type_name),
                );
                emitted_defs.insert(type_name);
            }
        }
        insert_before_contract_blocks(&mut output, missing_type_stubs);

        report_harness_budget(&output, selection);
        output
    }
}

fn insert_before_contract_blocks(output: &mut Vec<String>, blocks: Vec<String>) {
    if blocks.is_empty() {
        return;
    }

    let insert_at = output
        .iter()
        .position(|block| {
            block
                .lines()
                .find(|line| !line.trim().is_empty())
                .map(|line| starts_top_level_container_block(line.trim_start()))
                .unwrap_or(false)
        })
        .unwrap_or(output.len());

    for block in blocks.into_iter().rev() {
        if !output.iter().any(|existing| existing == &block) {
            output.insert(insert_at, block);
        }
    }
}

fn starts_top_level_container_block(line: &str) -> bool {
    line.starts_with("contract ")
        || line.starts_with("abstract contract ")
        || line.starts_with("interface ")
        || line.starts_with("library ")
}

fn report_harness_budget(output: &[String], selection: &SliceSelection) {
    if !selection.has_target_entry() {
        return;
    }

    let mut target_test_count = 0usize;
    let mut non_target_tests = Vec::new();
    let mut non_target_setups = Vec::new();

    for block in output {
        let contract_name = parse_rendered_contract_name(block);
        for line in block.lines() {
            let trimmed = line.trim_start();
            if !trimmed.starts_with("function ") && !trimmed.starts_with("constructor") {
                continue;
            }

            let function_name = if trimmed.starts_with("constructor") {
                "constructor".to_string()
            } else {
                extract_function_name_from_line(trimmed)
            };

            if function_name.is_empty() {
                continue;
            }

            if contract_name.as_deref() == Some(selection.target_contract.as_str())
                && function_name == selection.target_entry_function
            {
                target_test_count += 1;
            } else if is_test_like_function(&function_name) {
                non_target_tests.push(format!(
                    "{}.{}",
                    contract_name.as_deref().unwrap_or("<unknown>"),
                    function_name
                ));
            } else if is_setup_function(&function_name)
                && contract_name.as_deref() != Some(selection.target_contract.as_str())
            {
                non_target_setups.push(format!(
                    "{}.{}",
                    contract_name.as_deref().unwrap_or("<unknown>"),
                    function_name
                ));
            }
        }
    }

    println!(
        "📦 Harness budget: target test count={}, selected functions={}, contracts={}",
        target_test_count,
        selection.relevant_contract_functions.len(),
        selection.relevant_contracts.len()
    );
    if target_test_count != 1 {
        println!(
            "⚠️  Harness budget warning: expected exactly one target test {}.{}, found {}",
            selection.target_contract, selection.target_entry_function, target_test_count
        );
    }
    if !non_target_tests.is_empty() {
        println!(
            "⚠️  Harness budget warning: non-target test functions rendered: {:?}",
            non_target_tests
        );
    }
    if !non_target_setups.is_empty() {
        println!(
            "⚠️  Harness budget warning: non-target setup functions rendered: {:?}",
            non_target_setups
        );
    }
}

fn parse_rendered_contract_name(block: &str) -> Option<String> {
    for line in block.lines() {
        let trimmed = line.trim_start();
        for prefix in ["contract ", "abstract contract ", "interface ", "library "] {
            if let Some(rest) = trimmed.strip_prefix(prefix) {
                let name = rest
                    .split(|ch: char| !(ch.is_ascii_alphanumeric() || ch == '_'))
                    .next()
                    .unwrap_or("");
                if !name.is_empty() {
                    return Some(name.to_string());
                }
            }
        }
    }
    None
}

fn collect_using_libraries(
    using_directive: &ast::UsingDirective<'_>,
    libraries: &mut HashSet<String>,
) {
    if let ast::UsingList::Single(path) = &using_directive.list {
        if let Some(library_name) = path.to_string().split('.').next() {
            if !library_name.is_empty() {
                libraries.insert(library_name.to_string());
            }
        }
    }
}

fn top_level_item_from_ast(
    source_map: &SourceMap,
    item: &solar_ast::Item<'_>,
) -> Option<AstTopLevelItem> {
    let code = snippet_for_span(source_map, item.span)?;
    let mut type_refs = HashSet::new();

    match &item.kind {
        ItemKind::Struct(item) => {
            for field in item.fields.iter() {
                collect_type_refs_from_variable(field, &mut type_refs);
            }
            Some(AstTopLevelItem {
                name: Some(item.name.to_string()),
                type_refs,
                code,
            })
        }
        ItemKind::Enum(item) => Some(AstTopLevelItem {
            name: Some(item.name.to_string()),
            type_refs,
            code,
        }),
        ItemKind::Udvt(item) => {
            collect_type_refs_from_type(&item.ty, &mut type_refs);
            Some(AstTopLevelItem {
                name: Some(item.name.to_string()),
                type_refs,
                code,
            })
        }
        ItemKind::Error(item) => {
            collect_type_refs_from_parameter_list(&item.parameters, &mut type_refs);
            Some(AstTopLevelItem {
                name: Some(item.name.to_string()),
                type_refs,
                code,
            })
        }
        ItemKind::Event(item) => {
            collect_type_refs_from_parameter_list(&item.parameters, &mut type_refs);
            Some(AstTopLevelItem {
                name: Some(item.name.to_string()),
                type_refs,
                code,
            })
        }
        ItemKind::Variable(var) => {
            collect_type_refs_from_variable(var, &mut type_refs);
            Some(AstTopLevelItem {
                name: var.name.map(|name| name.to_string()),
                type_refs,
                code,
            })
        }
        ItemKind::Function(func) => {
            collect_type_refs_from_function(func, &mut type_refs);
            Some(AstTopLevelItem {
                name: Some(function_item_name(func)),
                type_refs,
                code,
            })
        }
        _ => None,
    }
}

fn snippet_for_span(source_map: &SourceMap, span: Span) -> Option<String> {
    source_map
        .span_to_snippet(span)
        .ok()
        .map(|snippet| snippet.trim().to_string())
        .filter(|snippet| !snippet.is_empty())
}

fn contract_signature_snippet(
    source_map: &SourceMap,
    item: &solar_ast::Item<'_>,
    contract: &ast::ItemContract<'_>,
) -> String {
    let signature_span = contract
        .body
        .first()
        .map(|first| Span::new(item.span.lo(), first.span.lo()))
        .unwrap_or(item.span);

    let mut signature = source_map
        .span_to_snippet(signature_span)
        .unwrap_or_else(|_| format!("{} {} {{", contract.kind.to_str(), contract.name));

    if !contract.body.is_empty() {
        if let Some(open_brace) = signature.rfind('{') {
            signature.truncate(open_brace + 1);
        }
    }

    signature.trim_end().to_string()
}

fn contract_body_item_from_ast(
    source_map: &SourceMap,
    item: &solar_ast::Item<'_>,
) -> Option<AstContractItem> {
    let code = snippet_for_span(source_map, item.span)?;

    match &item.kind {
        ItemKind::Function(func) => {
            let kind = match func.kind {
                FunctionKind::Modifier => AstContractItemKind::Modifier,
                _ => AstContractItemKind::Function,
            };
            let mut type_refs = HashSet::new();
            collect_type_refs_from_function(func, &mut type_refs);
            let name = function_item_name(func);
            Some(AstContractItem {
                kind,
                name: Some(name),
                type_name: None,
                type_refs,
                code,
            })
        }
        ItemKind::Variable(var) => {
            let mut type_refs = HashSet::new();
            collect_type_refs_from_variable(var, &mut type_refs);
            Some(AstContractItem {
                kind: AstContractItemKind::Variable,
                name: var.name.map(|name| name.to_string()),
                type_name: snippet_for_span(source_map, var.ty.span),
                type_refs,
                code,
            })
        }
        ItemKind::Struct(item) => {
            let mut type_refs = HashSet::new();
            for field in item.fields.iter() {
                collect_type_refs_from_variable(field, &mut type_refs);
            }
            Some(AstContractItem {
                kind: AstContractItemKind::Struct,
                name: Some(item.name.to_string()),
                type_name: None,
                type_refs,
                code,
            })
        }
        ItemKind::Enum(item) => Some(AstContractItem {
            kind: AstContractItemKind::Enum,
            name: Some(item.name.to_string()),
            type_name: None,
            type_refs: HashSet::new(),
            code,
        }),
        ItemKind::Udvt(item) => {
            let mut type_refs = HashSet::new();
            collect_type_refs_from_type(&item.ty, &mut type_refs);
            Some(AstContractItem {
                kind: AstContractItemKind::Udvt,
                name: Some(item.name.to_string()),
                type_name: None,
                type_refs,
                code,
            })
        }
        ItemKind::Error(item) => {
            let mut type_refs = HashSet::new();
            collect_type_refs_from_parameter_list(&item.parameters, &mut type_refs);
            Some(AstContractItem {
                kind: AstContractItemKind::Error,
                name: Some(item.name.to_string()),
                type_name: None,
                type_refs,
                code,
            })
        }
        ItemKind::Event(item) => {
            let mut type_refs = HashSet::new();
            collect_type_refs_from_parameter_list(&item.parameters, &mut type_refs);
            Some(AstContractItem {
                kind: AstContractItemKind::Event,
                name: Some(item.name.to_string()),
                type_name: None,
                type_refs,
                code,
            })
        }
        ItemKind::Using(_) => Some(AstContractItem {
            kind: AstContractItemKind::Using,
            name: None,
            type_name: None,
            type_refs: HashSet::new(),
            code,
        }),
        _ => None,
    }
}

fn function_item_name(func: &ast::ItemFunction<'_>) -> String {
    func.header
        .name
        .map(|name| name.to_string())
        .unwrap_or_else(|| func.kind.to_str().to_string())
}

fn collect_type_refs_from_function(func: &ast::ItemFunction<'_>, refs: &mut HashSet<String>) {
    collect_type_refs_from_parameter_list(&func.header.parameters, refs);
    if let Some(returns) = &func.header.returns {
        collect_type_refs_from_parameter_list(returns, refs);
    }
}

fn collect_type_refs_from_parameter_list(
    parameters: &ast::ParameterList<'_>,
    refs: &mut HashSet<String>,
) {
    for parameter in parameters.iter() {
        collect_type_refs_from_variable(parameter, refs);
    }
}

fn collect_type_refs_from_variable(var: &ast::VariableDefinition<'_>, refs: &mut HashSet<String>) {
    collect_type_refs_from_type(&var.ty, refs);
}

fn collect_type_refs_from_type(ty: &ast::Type<'_>, refs: &mut HashSet<String>) {
    match &ty.kind {
        ast::TypeKind::Custom(path) => {
            if let Some(name) = path.to_string().split('.').next() {
                if !name.is_empty() {
                    refs.insert(name.to_string());
                }
            }
        }
        ast::TypeKind::Array(array) => collect_type_refs_from_type(&array.element, refs),
        ast::TypeKind::Mapping(mapping) => {
            collect_type_refs_from_type(&mapping.key, refs);
            collect_type_refs_from_type(&mapping.value, refs);
        }
        ast::TypeKind::Function(function) => {
            collect_type_refs_from_parameter_list(&function.parameters, refs);
            if let Some(returns) = &function.returns {
                collect_type_refs_from_parameter_list(returns, refs);
            }
        }
        ast::TypeKind::Elementary(_) => {}
    }
}

fn should_stub_type(type_name: &str, emitted_defs: &HashSet<String>) -> bool {
    !type_name.is_empty()
        && !emitted_defs.contains(type_name)
        && !matches!(
            type_name,
            "address" | "bool" | "string" | "bytes" | "uint" | "uint256" | "int" | "int256"
        )
}

fn parse_base_contracts_from_signature(signature: &str) -> Vec<String> {
    let Some((_, tail)) = signature.split_once(" is ") else {
        return Vec::new();
    };
    let base_segment = tail.split('{').next().unwrap_or(tail);
    base_segment
        .split(',')
        .filter_map(|part| {
            let name = part
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

fn should_include_contract_item(
    contract_name: &str,
    item: &AstContractItem,
    selection: &SliceSelection,
    include_types: bool,
) -> bool {
    match item.kind {
        AstContractItemKind::Function => item.name.as_ref().map_or(false, |name| {
            if selection.has_target_entry() {
                selection.contains_contract_function(contract_name, name)
            } else {
                selection.relevant_functions.contains(name)
            }
        }),
        AstContractItemKind::Variable => item
            .name
            .as_ref()
            .map_or(false, |name| selection.relevant_variables.contains(name)),
        AstContractItemKind::Modifier => item.name.as_ref().map_or(false, |name| {
            if selection.has_target_entry() {
                selection.contains_contract_function(contract_name, name)
            } else {
                selection.relevant_functions.contains(name)
            }
        }),
        AstContractItemKind::Struct
        | AstContractItemKind::Enum
        | AstContractItemKind::Udvt
        | AstContractItemKind::Error
        | AstContractItemKind::Event
        | AstContractItemKind::Using => include_types,
    }
}

fn should_exclude_harness_item(
    contract_name: &str,
    item: &AstContractItem,
    selection: &SliceSelection,
) -> bool {
    if !selection.has_target_entry() || !matches!(item.kind, AstContractItemKind::Function) {
        return false;
    }

    let Some(name) = item.name.as_deref() else {
        return false;
    };

    if contract_name == selection.target_contract {
        return is_test_like_function(name)
            && name != selection.target_entry_function
            && !selection.contains_contract_function(contract_name, name);
    }

    if is_setup_function(name) {
        return !selection.contains_contract_function(contract_name, name);
    }

    is_test_like_function(name)
}

fn is_test_like_function(name: &str) -> bool {
    name == "test" || name.starts_with("test_") || name.starts_with("test")
}

fn is_setup_function(name: &str) -> bool {
    matches!(name, "setUp" | "beforeEach" | "constructor")
}

fn indent_contract_item(code: &str) -> String {
    code.lines()
        .map(|line| {
            if line.trim().is_empty() {
                String::new()
            } else {
                format!("    {}", line)
            }
        })
        .collect::<Vec<_>>()
        .join("\n")
}

fn push_unique(items: &mut Vec<String>, item: String) {
    if !items.iter().any(|existing| existing == &item) {
        items.push(item);
    }
}

fn push_unique_top_level(items: &mut Vec<AstTopLevelItem>, item: AstTopLevelItem) {
    if !items.iter().any(|existing| existing.code == item.code) {
        items.push(item);
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let matches = Command::new("SC_Slicer")
        .version("0.2.0")
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
                .help("Use deterministic semantic slicing")
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
                .help("Use two-phase processing: static slice first, then semantic analysis")
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
                .help("Enable source-backed AST-valid resurrection v2")
                .long("resurrect-v2")
                .action(clap::ArgAction::SetTrue),
        )
        .arg(
            Arg::new("compile_guarantee")
                .help("Allow resurrection v2 to widen monotonically up to the full source unit")
                .long("compile-guarantee")
                .action(clap::ArgAction::SetTrue),
        )
        .get_matches();

    let input_path = matches.get_one::<String>("input").unwrap();
    let contract_name = matches.get_one::<String>("contract_name").unwrap();
    let variable_name = matches.get_one::<String>("variable_name").unwrap();
    let function_name_str = matches.get_one::<String>("function_name");
    let target_test_from_arg = matches.get_one::<String>("target_test");
    let function_name = target_test_from_arg
        .or(function_name_str)
        .map(|s| s.as_str())
        .unwrap_or("");
    let slice_level = matches.get_one::<String>("slice_level").unwrap();
    let output_file = matches.get_one::<String>("output");
    let exclude_libs = matches.get_flag("exclude_libs");
    let include_types = matches.get_flag("include_types");
    let use_semantic = matches.get_flag("semantic");
    let use_two_phase = matches.get_flag("two_phase");
    let use_parallel = matches.get_flag("parallel");
    let use_prefilter = matches.get_flag("prefilter");
    let use_resurrect_v2 = matches.get_flag("resurrect_v2")
        || std::env::var("SC_SLICER_RESURRECT_V2")
            .map(|value| value != "0" && !value.trim().is_empty())
            .unwrap_or(false);
    let compile_guarantee = matches.get_flag("compile_guarantee") || use_resurrect_v2;
    let aggressive_cleanup = matches.get_flag("aggressive_noise_reduction");
    let llm_completion_requested = matches.get_flag("llm_completion");
    let max_level: usize = matches
        .get_one::<String>("max_level")
        .and_then(|s| s.parse().ok())
        .unwrap_or(3)
        .min(10);
    let llm_threshold: u8 = matches
        .get_one::<String>("llm_threshold")
        .and_then(|s| s.parse().ok())
        .unwrap_or(30)
        .min(100);
    let max_concurrent: usize = matches
        .get_one::<String>("max_concurrent")
        .and_then(|s| s.parse().ok())
        .unwrap_or(4)
        .max(1)
        .min(20);
    let cache_file = matches.get_one::<String>("cache_file").map(|s| s.as_str());
    let api_key_from_arg = matches
        .get_one::<String>("api_key")
        .map(|s| s.as_str())
        .unwrap_or("");
    let api_key = if !api_key_from_arg.is_empty() {
        api_key_from_arg.to_string()
    } else {
        std::env::var("OPENAI_API_KEY").unwrap_or_else(|_| String::new())
    };
    let base_url =
        std::env::var("OPENAI_BASE_URL").unwrap_or_else(|_| "https://api.deepseek.com".to_string());
    let model_name = matches.get_one::<String>("model").unwrap().to_string();

    let execution_log_path = resolve_execution_log_path(
        contract_name,
        function_name,
        variable_name,
        if use_semantic { "full" } else { "quick" },
        output_file.map(|s| s.as_str()),
    );
    let execution_log_path =
        execution_log::init(execution_log_path, &std::env::args().collect::<Vec<_>>())?;
    println!("📝 Execution log: {}", execution_log_path.display());
    execution_log::phase_start("configuration");
    execution_log::log_line(format!(
        "config input={} contract={} function={} variable={} semantic={} two_phase={} resurrect_v2={} compile_guarantee={} output={}",
        input_path,
        contract_name,
        if function_name.is_empty() { "<all>" } else { function_name },
        variable_name,
        use_semantic,
        use_two_phase,
        use_resurrect_v2,
        compile_guarantee,
        output_file.map(|s| s.as_str()).unwrap_or("<stdout>")
    ));
    execution_log::detail(
        "runtime",
        format!(
            "model={} base_url={} llm_threshold={} parallel={} max_concurrent={} cache={} max_level={} aggressive_cleanup={} llm_completion_requested={} llm_completion_disabled=true",
            model_name,
            base_url,
            llm_threshold,
            use_parallel,
            max_concurrent,
            cache_file.unwrap_or("<none>"),
            max_level,
            aggressive_cleanup,
            llm_completion_requested
        ),
    );
    execution_log::phase_end("configuration", "ok");

    // Collect all .sol files
    execution_log::phase_start("input_collection");
    let file_paths = collect_sol_files(input_path)?;

    if file_paths.is_empty() {
        eprintln!("❌ No .sol files found in {}", input_path);
        execution_log::log_line(format!("error no .sol files found in {}", input_path));
        return Err("No .sol files found".into());
    }

    // 读取所有源代码
    let mut source_codes = Vec::new();
    for file_path in &file_paths {
        let source_code = fs::read_to_string(file_path)
            .map_err(|e| format!("Failed to read file {}: {}", file_path, e))?;
        source_codes.push(source_code);
    }
    log_input_files(&file_paths, &source_codes);
    let combined_source = source_codes.join("\n");
    execution_log::phase_end(
        "input_collection",
        format!(
            "files={} combined_lines={} combined_bytes={}",
            file_paths.len(),
            combined_source.lines().count(),
            combined_source.len()
        ),
    );

    // 解析AST并分析
    execution_log::phase_start("ast_parse_and_pdg_analysis");
    let sess = solar_interface::Session::builder()
        .with_buffer_emitter(solar_interface::ColorChoice::Auto)
        .build();
    let result = sess.enter(
        || -> solar_interface::Result<(AnalysisResult, AstSliceIndex)> {
            let arena = solar_ast::Arena::new();
            let mut all_asts = Vec::new();
            for file_path in &file_paths {
                let mut parser =
                    solar_parse::Parser::from_file(&sess, &arena, Path::new(file_path))?;
                let ast = parser.parse_file().map_err(|e| e.emit())?;
                all_asts.push(ast);
            }
            // 使用目标导向的分析
            let analysis = analyzer::analyze_asts_targeted(
                &all_asts,
                &combined_source,
                contract_name,
                function_name,
                variable_name,
            );
            let ast_index = AstSliceIndex::from_asts(&all_asts, sess.source_map());
            Ok((analysis, ast_index))
        },
    );

    let (analysis, ast_index) = match result {
        Ok(result) => result,
        Err(_) => {
            execution_log::log_line("error failed to parse or analyze contracts");
            return Err("Failed to parse or analyze the contracts".into());
        }
    };
    execution_log::log_line(format!(
        "analysis parsed files={} pdg_nodes={} pdg_edges={}",
        file_paths.len(),
        analysis.program_dependency_graph.nodes.len(),
        analysis.program_dependency_graph.edges.len()
    ));
    log_ast_index_summary(&ast_index);
    log_pdg_summary(&analysis, contract_name, function_name, variable_name);
    execution_log::phase_end(
        "ast_parse_and_pdg_analysis",
        format!(
            "pdg_nodes={} pdg_edges={} contracts={}",
            analysis.program_dependency_graph.nodes.len(),
            analysis.program_dependency_graph.edges.len(),
            ast_index.contracts.len()
        ),
    );

    let target = TargetSpec {
        contract: contract_name.to_string(),
        entry_function: function_name.to_string(),
        focus_symbol: variable_name.to_string(),
    };
    let harness_policy = HarnessPolicy::default();

    if !target.entry_function.is_empty()
        && !ast_index.contract_has_function(&target.contract, &target.entry_function)
    {
        execution_log::log_line(format!(
            "error target function not found target={}.{}",
            target.contract, target.entry_function
        ));
        return Err(format!(
            "Target function '{}.{}' was not found; refusing to fall back to variable-wide slicing",
            target.contract, target.entry_function
        )
        .into());
    }

    let slice = if use_semantic {
        if use_two_phase {
            execution_log::phase_start("semantic_two_phase");
            println!("🔄 Using two-phase processing for large files...");
            if use_parallel {
                println!(
                    "⚡ Parallel processing enabled: {} concurrent requests",
                    max_concurrent
                );
            }
            if use_prefilter {
                println!("🔍 Pre-filtering enabled");
            }
            if let Some(cache) = cache_file {
                println!("💾 Using cache file: {}", cache);
            }

            // 第一阶段：快速静态切片
            println!("📍 Phase 1: Static slicing to identify relevant code...");
            execution_log::phase_start("phase1_static_slice");
            let static_slice = analyzer::get_source_slice(
                &analysis,
                &combined_source,
                contract_name,
                function_name,
                variable_name,
                exclude_libs,
                include_types,
            );
            println!(
                "✅ Phase 1 complete: {} code blocks identified",
                static_slice.len()
            );
            execution_log::phase_end(
                "phase1_static_slice",
                format!(
                    "blocks={} lines={}",
                    static_slice.len(),
                    count_block_lines(&static_slice)
                ),
            );

            // 提取静态切片中的合约和函数信息
            let (phase1_contracts, phase1_functions) =
                extract_contracts_and_functions(&static_slice);
            println!("📊 Relevant contracts: {:?}", phase1_contracts);
            println!(
                "📊 Relevant functions: {} functions",
                phase1_functions.len()
            );
            execution_log::sample("phase1_contracts", &phase1_contracts, 40);
            execution_log::sample("phase1_functions", &phase1_functions, 60);

            // 三层漏斗过滤
            execution_log::phase_start("contract_filter");
            let filter_result = if use_prefilter {
                three_layer_filter(&phase1_contracts, contract_name)
            } else {
                // 不启用预过滤时，全部进入白名单
                ThreeLayerFilterResult {
                    blacklist: std::collections::HashSet::new(),
                    whitelist: phase1_contracts.clone(),
                    graylist: std::collections::HashSet::new(),
                }
            };

            let graylist_kept = std::collections::HashSet::new();
            if !filter_result.graylist.is_empty() {
                println!(
                    "🔒 Graylist arbitration disabled; dropping {} uncertain contracts",
                    filter_result.graylist.len()
                );
                execution_log::log_line(format!(
                    "contract_filter graylist_arbitration_disabled dropped={}",
                    filter_result.graylist.len()
                ));
            }
            execution_log::detail(
                "contract_filter",
                format!(
                    "blacklist={} whitelist={} graylist={} graylist_kept=0 llm_disabled=true",
                    filter_result.blacklist.len(),
                    filter_result.whitelist.len(),
                    filter_result.graylist.len()
                ),
            );
            execution_log::sample("contract_filter_blacklist", &filter_result.blacklist, 25);
            execution_log::sample("contract_filter_graylist", &filter_result.graylist, 25);

            // 合并最终过滤结果：只保留确定性白名单。
            let mut filtered_contracts = filter_result.whitelist.clone();
            filtered_contracts.extend(graylist_kept);

            println!(
                "📊 Final filtered contracts: {} contracts\n",
                filtered_contracts.len()
            );
            execution_log::sample("contract_filter_final", &filtered_contracts, 40);
            execution_log::phase_end(
                "contract_filter",
                format!("final_contracts={}", filtered_contracts.len()),
            );

            // 第二阶段：只对相关代码进行语义分析
            println!("📍 Phase 2: Semantic analysis on relevant code only...");
            execution_log::phase_start("phase2_semantic_slice");
            let adapter = PdgAdapter {
                analysis: &analysis,
                source_code: &combined_source,
            };
            let model = model_name.clone();
            let mut slicer = crate::semantic_slicer::SemanticSlicer::new_with_options(
                &adapter,
                api_key.to_string(),
                base_url.to_string(),
                model,
                llm_threshold,
                use_parallel,
                max_concurrent,
                cache_file.map(|s| s.to_string()),
            );

            let sink_nodes = find_harness_seed_nodes(&analysis, &target);
            log_seed_nodes(&analysis, &sink_nodes, "semantic_two_phase_seed_nodes");

            // 使用新的函数级混合切片（CHSS），传入Phase 1过滤的合约列表
            let slice_atoms = slicer
                .run_slicing_with_max_depth(sink_nodes, max_level)
                .await;
            println!("✅ Phase 2 complete: Function-Level CHSS finished");

            let slice_nodes: std::collections::HashSet<usize> = slice_atoms
                .into_iter()
                .filter_map(|atom| match atom {
                    crate::semantic_slicer::SliceAtom::FullStatement(id) => Some(id),
                    crate::semantic_slicer::SliceAtom::FullVariableDeclStatement(id) => Some(id),
                    crate::semantic_slicer::SliceAtom::FullExpressionStatement(id) => Some(id),
                    crate::semantic_slicer::SliceAtom::FullReturnStatement(id) => Some(id),
                    crate::semantic_slicer::SliceAtom::FullIfStatement(id) => Some(id),
                    crate::semantic_slicer::SliceAtom::FullForStatement(id) => Some(id),
                    crate::semantic_slicer::SliceAtom::FullBlockWindow {
                        block_id: _,
                        start_stmt: _,
                        end_stmt: _,
                    } => None,
                })
                .collect();

            log_seed_nodes(
                &analysis,
                &slice_nodes.iter().copied().collect::<Vec<_>>(),
                "semantic_selected_nodes",
            );
            execution_log::phase_end(
                "phase2_semantic_slice",
                format!("selected_nodes={}", slice_nodes.len()),
            );

            // 转换为 Vec<String> 格式以保持兼容性
            let rendered = get_source_from_nodes(
                &mut slicer,
                &analysis,
                &ast_index,
                &combined_source,
                &slice_nodes,
                &target,
                &harness_policy,
                exclude_libs,
                include_types,
                max_level,
                aggressive_cleanup,
            )
            .await;
            execution_log::phase_end(
                "semantic_two_phase",
                format!(
                    "rendered_blocks={} rendered_lines={}",
                    rendered.len(),
                    count_block_lines(&rendered)
                ),
            );
            rendered
        } else {
            execution_log::phase_start("semantic_single_phase");
            // 使用语义切片（传统单阶段）- 保留旧逻辑作为后备
            let adapter = PdgAdapter {
                analysis: &analysis,
                source_code: &combined_source,
            };
            let model = model_name.clone();
            let mut slicer = crate::semantic_slicer::SemanticSlicer::new_with_threshold(
                &adapter,
                api_key.to_string(),
                base_url.to_string(),
                model,
                llm_threshold,
            );
            let sink_nodes = find_harness_seed_nodes(&analysis, &target);
            log_seed_nodes(&analysis, &sink_nodes, "semantic_single_phase_seed_nodes");

            // 使用语义切片
            let slice_atoms = slicer
                .run_slicing_with_max_depth(sink_nodes, max_level)
                .await;
            let slice_nodes: std::collections::HashSet<usize> = slice_atoms
                .into_iter()
                .filter_map(|atom| match atom {
                    crate::semantic_slicer::SliceAtom::FullStatement(id) => Some(id),
                    crate::semantic_slicer::SliceAtom::FullVariableDeclStatement(id) => Some(id),
                    crate::semantic_slicer::SliceAtom::FullExpressionStatement(id) => Some(id),
                    crate::semantic_slicer::SliceAtom::FullReturnStatement(id) => Some(id),
                    crate::semantic_slicer::SliceAtom::FullIfStatement(id) => Some(id),
                    crate::semantic_slicer::SliceAtom::FullForStatement(id) => Some(id),
                    crate::semantic_slicer::SliceAtom::FullBlockWindow {
                        block_id: _,
                        start_stmt: _,
                        end_stmt: _,
                    } => None,
                })
                .collect();
            log_seed_nodes(
                &analysis,
                &slice_nodes.iter().copied().collect::<Vec<_>>(),
                "semantic_single_phase_selected_nodes",
            );
            let rendered = get_source_from_nodes(
                &mut slicer,
                &analysis,
                &ast_index,
                &combined_source,
                &slice_nodes,
                &target,
                &harness_policy,
                exclude_libs,
                include_types,
                max_level,
                aggressive_cleanup,
            )
            .await;
            execution_log::phase_end(
                "semantic_single_phase",
                format!(
                    "selected_nodes={} rendered_blocks={} rendered_lines={}",
                    slice_nodes.len(),
                    rendered.len(),
                    count_block_lines(&rendered)
                ),
            );
            rendered
        }
    } else {
        execution_log::phase_start("static_slice");
        match slice_level.as_str() {
            "line" => {
                let slice_node_ids =
                    collect_static_slice_node_ids(&analysis, function_name, variable_name);
                log_pdg_node_ids(&analysis, &slice_node_ids, "static_slice_node_ids");
                log_pdg_node_ids(&analysis, &slice_node_ids, "static_slice_node_ids");
                let selection = build_slice_selection(
                    &analysis,
                    &ast_index,
                    &slice_node_ids,
                    &target,
                    &harness_policy,
                    max_level,
                );
                log_slice_selection(&selection, "static_line_selection");
                let rendered = ast_index.render(&selection, include_types, exclude_libs, max_level);
                execution_log::phase_end(
                    "static_slice",
                    format!(
                        "mode=line nodes={} rendered_blocks={} rendered_lines={}",
                        slice_node_ids.len(),
                        rendered.len(),
                        count_block_lines(&rendered)
                    ),
                );
                rendered
            }
            "function" | _ => {
                let slice_node_ids =
                    collect_static_slice_node_ids(&analysis, function_name, variable_name);
                log_pdg_node_ids(&analysis, &slice_node_ids, "static_slice_node_ids");
                log_pdg_node_ids(&analysis, &slice_node_ids, "static_slice_node_ids");
                let selection = build_slice_selection(
                    &analysis,
                    &ast_index,
                    &slice_node_ids,
                    &target,
                    &harness_policy,
                    max_level,
                );
                log_slice_selection(&selection, "static_function_selection");
                let rendered = ast_index.render(&selection, include_types, exclude_libs, max_level);
                execution_log::phase_end(
                    "static_slice",
                    format!(
                        "mode=function nodes={} rendered_blocks={} rendered_lines={}",
                        slice_node_ids.len(),
                        rendered.len(),
                        count_block_lines(&rendered)
                    ),
                );
                rendered
            }
        }
    };

    let mut log_file = OpenOptions::new()
        .create(true)
        .append(true)
        .open("analysis.log")?;

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

    let slice_code = slice.join("\n");
    execution_log::detail(
        "pre_completion_slice",
        format!(
            "blocks={} lines={} bytes={}",
            slice.len(),
            slice_code.lines().count(),
            slice_code.len()
        ),
    );
    if use_semantic {
        println!("🔒 Skipping missing-type code completion; deterministic slicing is enforced.");
        execution_log::phase_start("code_completion_missing_types");
        execution_log::phase_end(
            "code_completion_missing_types",
            format!(
                "disabled_no_mutation input_lines={} output_lines={} delta_lines=0",
                slice_code.lines().count(),
                slice_code.lines().count()
            ),
        );
    }
    let final_output = slice_code;

    if llm_completion_requested {
        execution_log::phase_start("llm_completion_pipeline");
        writeln!(
            log_file,
            "LLM completion requested but ignored: LLM participation is disabled"
        )?;
        execution_log::phase_end("llm_completion_pipeline", "disabled_no_mutation");
    }

    let normalized_output = source_normalizer::normalize_source(&final_output);
    let final_output =
        if normalized_output.report.has_changes() {
            println!(
                "🧹 Final preflight normalized {} malformed/comment lines",
                normalized_output.report.actions.len()
            );
            writeln!(
                log_file,
                "🧹 Final preflight normalized {} malformed/comment lines",
                normalized_output.report.actions.len()
            )?;
            execution_log::detail(
                "final_preflight_normalize",
                format!("actions={}", normalized_output.report.actions.len()),
            );
            execution_log::sample(
                "final_preflight_actions",
                normalized_output.report.actions.iter().map(|action| {
                    format!("{:?}@{}:{}", action.kind, action.line, action.text.trim())
                }),
                20,
            );
            normalized_output.code
        } else {
            final_output
        };
    let final_output = repair_dangling_value_continuations(&final_output, &combined_source);

    // Source-backed Code Resurrection V2
    let final_output = if use_resurrect_v2 {
        println!("🚀 Starting source-backed Resurrection V2...");
        execution_log::log_line("resurrection_v2 pipeline started");
        let output_path = match output_file {
            Some(path) => std::path::PathBuf::from(path),
            None => std::path::PathBuf::from("results/ResurrectedV2.t.sol"),
        };
        let request = sol_resurrect_v2::ResurrectionV2Request {
            input_files: file_paths.iter().map(PathBuf::from).collect(),
            project_root: infer_project_root(input_path),
            seed_slice: final_output.clone(),
            target_contract: target.contract.clone(),
            target_test: target.entry_function.clone(),
            focus_symbol: target.focus_symbol.clone(),
            output_path: output_path.clone(),
            compile_guarantee,
        };

        match sol_resurrect_v2::run_resurrection_v2(request).await {
            Ok(result) => {
                writeln!(
                    log_file,
                    "✅ Resurrection V2 returned output: compile_success={} fallback_level={} ({})",
                    result.metadata.compile_success,
                    result.metadata.fallback_level,
                    result.metadata.fallback_level_name
                )?;
                execution_log::log_line(format!(
                    "resurrection_v2 returned lines={} compile_success={} fallback_level={}",
                    result.code.lines().count(),
                    result.metadata.compile_success,
                    result.metadata.fallback_level
                ));
                result.code
            }
            Err(e) => {
                eprintln!("⚠️ Resurrection V2 failed: {}", e);
                writeln!(log_file, "⚠️ Resurrection V2 failed: {}", e)?;
                execution_log::log_line(format!("resurrection_v2 failed: {}", e));
                final_output
            }
        }
    } else {
        final_output
    };

    // Legacy token repair is explicitly outside resurrection v2. The v2 renderer only emits
    // complete source-backed atoms and widens the graph/fallback level on compiler feedback.
    let final_output = if use_resurrect_v2 {
        final_output
    } else {
        repair_dangling_value_continuations(&final_output, &combined_source)
    };

    if let Some(output_file) = output_file {
        fs::write(output_file, final_output.clone()).expect("Failed to write to file");
        writeln!(log_file, "✅ Results written to {}", output_file)?;
        execution_log::log_line(format!(
            "results written output={} lines={}",
            output_file,
            final_output.lines().count()
        ));
    } else {
        writeln!(log_file, "🔍 Source Code Slice Analysis")?;
        writeln!(log_file, "📁 Input: {}", input_path)?;
        writeln!(log_file, "🏢 Contract: {}", contract_name)?;
        writeln!(
            log_file,
            "⚡ Target test/function: {}",
            if function_name.is_empty() {
                "All functions"
            } else {
                function_name
            }
        )?;
        writeln!(log_file, "📊 Focus symbol: {}", variable_name)?;
        writeln!(log_file, "🎯 Slice Level: {}", slice_level)?;
        writeln!(
            log_file,
            "📋 Slice Results ({} lines):",
            final_output.lines().count()
        )?;
        writeln!(log_file, "{}", "=".repeat(60))?;

        for line in final_output.lines() {
            writeln!(log_file, "{}", line)?;
        }

        writeln!(log_file, "{}", "=".repeat(60))?;
        writeln!(log_file, "✅ Analysis completed successfully!")?;
    }
    execution_log::log_line("execution completed");
    Ok(())
}

fn resolve_execution_log_path(
    contract_name: &str,
    function_name: &str,
    variable_name: &str,
    run_mode: &str,
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
        "slice_{}_{}_{}_{}_{}.log",
        sanitize_log_name(contract_name),
        sanitize_log_name(function_part),
        sanitize_log_name(variable_name),
        sanitize_log_name(run_mode),
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

fn count_block_lines(blocks: &[String]) -> usize {
    blocks.iter().map(|block| block.lines().count()).sum()
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

fn log_ast_index_summary(ast_index: &AstSliceIndex) {
    let mut item_counts: HashMap<&'static str, usize> = HashMap::new();
    let mut contract_summaries = Vec::new();

    for contract in &ast_index.contracts {
        let mut functions = 0usize;
        let mut variables = 0usize;
        for item in &contract.body_items {
            match item.kind {
                AstContractItemKind::Function => functions += 1,
                AstContractItemKind::Variable => variables += 1,
                AstContractItemKind::Modifier => {
                    *item_counts.entry("modifier").or_default() += 1;
                }
                AstContractItemKind::Struct => {
                    *item_counts.entry("struct").or_default() += 1;
                }
                AstContractItemKind::Enum => {
                    *item_counts.entry("enum").or_default() += 1;
                }
                AstContractItemKind::Udvt => {
                    *item_counts.entry("udvt").or_default() += 1;
                }
                AstContractItemKind::Error => {
                    *item_counts.entry("error").or_default() += 1;
                }
                AstContractItemKind::Event => {
                    *item_counts.entry("event").or_default() += 1;
                }
                AstContractItemKind::Using => {
                    *item_counts.entry("using").or_default() += 1;
                }
            }
        }
        *item_counts.entry("function").or_default() += functions;
        *item_counts.entry("variable").or_default() += variables;
        contract_summaries.push(format!(
            "{}({:?}, functions={}, vars={}, items={})",
            contract.name,
            contract.kind,
            functions,
            variables,
            contract.body_items.len()
        ));
    }

    execution_log::detail(
        "ast_index",
        format!(
            "headers={} top_level_types={} contracts={} variable_types={} using_libraries={} item_counts={}",
            ast_index.top_level_headers.len(),
            ast_index.top_level_types.len(),
            ast_index.contracts.len(),
            ast_index.variable_types.len(),
            ast_index.using_libraries.len(),
            format_counts(&item_counts)
        ),
    );
    execution_log::sample("ast_contracts", contract_summaries, 60);
    execution_log::sample("ast_using_libraries", &ast_index.using_libraries, 30);
}

fn log_pdg_summary(
    analysis: &AnalysisResult,
    contract_name: &str,
    function_name: &str,
    variable_name: &str,
) {
    let mut node_counts: HashMap<&'static str, usize> = HashMap::new();
    let mut edge_counts: HashMap<&'static str, usize> = HashMap::new();
    let mut target_context_nodes = Vec::new();
    let mut variable_nodes = Vec::new();

    for (&node_id, node) in &analysis.program_dependency_graph.nodes {
        *node_counts.entry(node_kind_name(&node.kind)).or_default() += 1;
        if node.contract_context.as_deref() == Some(contract_name)
            && (function_name.is_empty() || node.function_context.as_deref() == Some(function_name))
        {
            target_context_nodes.push(format!(
                "{}:{}:{}:{}",
                node_id,
                node_kind_name(&node.kind),
                node.function_context.as_deref().unwrap_or("<none>"),
                compact_text(&node.label, 120)
            ));
        }
        if !variable_name.is_empty() && node.label.contains(variable_name) {
            variable_nodes.push(format!(
                "{}:{}:{}:{}",
                node_id,
                node_kind_name(&node.kind),
                node.function_context.as_deref().unwrap_or("<none>"),
                compact_text(&node.label, 120)
            ));
        }
    }

    for edge in &analysis.program_dependency_graph.edges {
        *edge_counts.entry(edge_kind_name(&edge.kind)).or_default() += 1;
    }

    execution_log::detail(
        "pdg_summary",
        format!(
            "nodes={} edges={} node_counts={} edge_counts={}",
            analysis.program_dependency_graph.nodes.len(),
            analysis.program_dependency_graph.edges.len(),
            format_counts(&node_counts),
            format_counts(&edge_counts)
        ),
    );
    execution_log::sample("pdg_target_context_nodes", target_context_nodes, 60);
    execution_log::sample("pdg_focus_symbol_nodes", variable_nodes, 60);
}

fn log_seed_nodes(analysis: &AnalysisResult, graph_node_indices: &[usize], name: &str) {
    let entries = graph_node_indices
        .iter()
        .filter_map(|graph_idx| {
            let node_idx = petgraph::graph::NodeIndex::new(*graph_idx);
            let stored_id = analysis
                .program_dependency_graph
                .graph
                .node_weight(node_idx)?;
            let node = analysis.program_dependency_graph.nodes.get(stored_id)?;
            Some(format!(
                "graph={} pdg={} kind={} contract={} function={} label={}",
                graph_idx,
                stored_id,
                node_kind_name(&node.kind),
                node.contract_context.as_deref().unwrap_or("<none>"),
                node.function_context.as_deref().unwrap_or("<none>"),
                compact_text(&node.label, 120)
            ))
        })
        .collect::<Vec<_>>();
    execution_log::sample(name, entries, 80);
}

fn log_pdg_node_ids(analysis: &AnalysisResult, pdg_node_ids: &HashSet<usize>, name: &str) {
    let entries = pdg_node_ids
        .iter()
        .filter_map(|node_id| {
            let node = analysis.program_dependency_graph.nodes.get(node_id)?;
            Some(format!(
                "pdg={} kind={} contract={} function={} label={}",
                node_id,
                node_kind_name(&node.kind),
                node.contract_context.as_deref().unwrap_or("<none>"),
                node.function_context.as_deref().unwrap_or("<none>"),
                compact_text(&node.label, 120)
            ))
        })
        .collect::<Vec<_>>();
    execution_log::sample(name, entries, 80);
}

fn log_slice_selection(selection: &SliceSelection, name: &str) {
    execution_log::detail(
        name,
        format!(
            "contracts={} full_contracts={} functions={} contract_functions={} variables={} dependency_traces={}",
            selection.relevant_contracts.len(),
            selection.full_contracts.len(),
            selection.relevant_functions.len(),
            selection.relevant_contract_functions.len(),
            selection.relevant_variables.len(),
            selection.dependency_traces.len()
        ),
    );
    execution_log::sample(
        &format!("{}_contracts", name),
        &selection.relevant_contracts,
        80,
    );
    execution_log::sample(
        &format!("{}_full_contracts", name),
        &selection.full_contracts,
        80,
    );
    execution_log::sample(
        &format!("{}_contract_functions", name),
        &selection.relevant_contract_functions,
        120,
    );
    execution_log::sample(
        &format!("{}_variables", name),
        &selection.relevant_variables,
        80,
    );
    execution_log::sample(
        &format!("{}_dependency_traces", name),
        selection
            .dependency_traces
            .iter()
            .map(|(key, reason)| format!("{} => {}", key, reason)),
        120,
    );
}

fn format_counts(counts: &HashMap<&'static str, usize>) -> String {
    let mut entries = counts
        .iter()
        .map(|(name, count)| format!("{}={}", name, count))
        .collect::<Vec<_>>();
    entries.sort();
    entries.join(",")
}

fn node_kind_name(kind: &crate::analyzer::NodeKind) -> &'static str {
    match kind {
        crate::analyzer::NodeKind::Assignment => "Assignment",
        crate::analyzer::NodeKind::FunctionCall => "FunctionCall",
        crate::analyzer::NodeKind::ControlCondition => "ControlCondition",
        crate::analyzer::NodeKind::ExternalCall => "ExternalCall",
        crate::analyzer::NodeKind::Return => "Return",
        crate::analyzer::NodeKind::VariableRead => "VariableRead",
        crate::analyzer::NodeKind::TaintSource => "TaintSource",
        crate::analyzer::NodeKind::TaintSink => "TaintSink",
        crate::analyzer::NodeKind::ConstraintNode => "ConstraintNode",
        crate::analyzer::NodeKind::StorageRead(_) => "StorageRead",
        crate::analyzer::NodeKind::StorageWrite(_) => "StorageWrite",
        crate::analyzer::NodeKind::VariableWrite(_) => "VariableWrite",
    }
}

fn edge_kind_name(kind: &crate::analyzer::EdgeKind) -> &'static str {
    match kind {
        crate::analyzer::EdgeKind::DataDependency(_) => "DataDependency",
        crate::analyzer::EdgeKind::ControlDependency => "ControlDependency",
        crate::analyzer::EdgeKind::ParameterIn => "ParameterIn",
        crate::analyzer::EdgeKind::ParameterOut => "ParameterOut",
        crate::analyzer::EdgeKind::Call => "Call",
        crate::analyzer::EdgeKind::TaintPropagation => "TaintPropagation",
        crate::analyzer::EdgeKind::ValidatedDataDependency(_) => "ValidatedDataDependency",
        crate::analyzer::EdgeKind::Return => "Return",
        crate::analyzer::EdgeKind::StorageDependency(_) => "StorageDependency",
    }
}

fn compact_text(text: &str, max_chars: usize) -> String {
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

fn repair_dangling_value_continuations(code: &str, original_source: &str) -> String {
    let mut source_declaration_heads: HashMap<String, String> = HashMap::new();
    // multiline type-then-visibility declarations: `mapping(...)\n    public varName;`
    let mut source_type_heads: HashMap<String, String> = HashMap::new();
    let source_lines: Vec<&str> = original_source.lines().collect();

    for (idx, line) in source_lines.iter().enumerate() {
        let trimmed = line.trim();

        // Numeric/literal constant value continuations (ends with `;`, starts with digit/quote)
        if looks_like_value_continuation(trimmed) {
            if let Some(head) = previous_nonempty_line(&source_lines, idx) {
                let head_trimmed = head.trim();
                if looks_like_multiline_declaration_head(head_trimmed) {
                    source_declaration_heads
                        .entry(trimmed.to_string())
                        .or_insert_with(|| head.to_string());
                }
            }
        }

        // Visibility+name tail: `public varName;` / `internal _state;`
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

    if source_declaration_heads.is_empty() && source_type_heads.is_empty() {
        return code.to_string();
    }

    let lines: Vec<&str> = code.lines().collect();
    let mut repaired = Vec::with_capacity(lines.len());
    let mut inserted = 0usize;

    for (idx, line) in lines.iter().enumerate() {
        let trimmed = line.trim();

        if looks_like_value_continuation(trimmed)
            && !previous_output_line_is_declaration_head(&lines, idx)
        {
            if let Some(head) = source_declaration_heads.get(trimmed) {
                repaired.push(head.clone());
                inserted += 1;
            }
        }

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
            "🧩 Final preflight restored {} multiline declaration heads",
            inserted
        );
    }

    repaired.join("\n")
}

fn previous_nonempty_line<'a>(lines: &'a [&str], idx: usize) -> Option<&'a str> {
    lines[..idx]
        .iter()
        .rev()
        .copied()
        .find(|line| !line.trim().is_empty())
}

fn previous_output_line_is_declaration_head(lines: &[&str], idx: usize) -> bool {
    previous_nonempty_line(lines, idx)
        .map(|line| looks_like_multiline_declaration_head(line.trim()))
        .unwrap_or(false)
}

fn previous_output_line_is_type_head(lines: &[&str], idx: usize) -> bool {
    previous_nonempty_line(lines, idx)
        .map(|line| looks_like_multiline_type_head(line.trim()))
        .unwrap_or(false)
}

fn looks_like_value_continuation(trimmed: &str) -> bool {
    if !trimmed.ends_with(';') || trimmed.contains('=') || trimmed.contains('{') {
        return false;
    }

    trimmed
        .chars()
        .next()
        .map(|ch| ch.is_ascii_digit() || ch == '"' || ch == '\'' || ch == '-')
        .unwrap_or(false)
        || trimmed.starts_with("0x")
        || trimmed.starts_with("address(")
        || trimmed.starts_with("bytes")
}

fn looks_like_multiline_declaration_head(trimmed: &str) -> bool {
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

/// Returns true for lines like `    public queuedWithdrawal;` — the trailing
/// visibility+name half of a multiline type declaration.
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

/// Returns true for `mapping(address => mapping(...))` style lines that are the
/// type-head of a multiline variable declaration.
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
    (trimmed.ends_with(')') || trimmed.ends_with(']') || trimmed.ends_with('>'))
        && (trimmed.starts_with("mapping(") || trimmed.contains(" => ") || trimmed.ends_with(')'))
}

fn collect_static_slice_node_ids(
    analysis: &AnalysisResult,
    function: &str,
    variable: &str,
) -> HashSet<usize> {
    let mut all_candidate_nodes = Vec::new();

    for (&node_id, node) in &analysis.program_dependency_graph.nodes {
        if node.label.contains(variable) {
            all_candidate_nodes.push(node_id);
        }
    }

    let mut candidate_nodes = if function.is_empty() {
        all_candidate_nodes.clone()
    } else {
        all_candidate_nodes
            .iter()
            .copied()
            .filter(|node_id| {
                analysis
                    .program_dependency_graph
                    .nodes
                    .get(node_id)
                    .and_then(|node| node.function_context.as_ref())
                    .map(|context| context == function)
                    .unwrap_or(false)
            })
            .collect()
    };

    if candidate_nodes.is_empty() && !function.is_empty() {
        candidate_nodes = all_candidate_nodes;
    }

    let mut all_slice_nodes = HashSet::new();
    for node_id in candidate_nodes {
        all_slice_nodes.extend(analysis.program_dependency_graph.backward_slice(node_id));
    }

    let mut related_vars = HashSet::new();
    for node_id in &all_slice_nodes {
        if let Some(node) = analysis.program_dependency_graph.nodes.get(node_id) {
            match &node.kind {
                crate::analyzer::NodeKind::StorageRead(var)
                | crate::analyzer::NodeKind::StorageWrite(var)
                | crate::analyzer::NodeKind::VariableWrite(var) => {
                    related_vars.insert(var.clone());
                }
                _ => {}
            }
        }
    }

    for var in &related_vars {
        for (&node_id, node) in &analysis.program_dependency_graph.nodes {
            if matches!(node.kind, crate::analyzer::NodeKind::StorageWrite(ref v) if v == var)
                || matches!(node.kind, crate::analyzer::NodeKind::VariableWrite(ref v) if v == var)
            {
                all_slice_nodes.extend(analysis.program_dependency_graph.backward_slice(node_id));
            }
        }
    }

    all_slice_nodes
}

fn graph_indices_to_pdg_node_ids(
    analysis: &AnalysisResult,
    graph_indices: &HashSet<usize>,
) -> HashSet<usize> {
    let mut node_ids = HashSet::new();
    for graph_index in graph_indices {
        if let Some(&node_id) = analysis
            .program_dependency_graph
            .graph
            .node_weight(petgraph::graph::NodeIndex::new(*graph_index))
        {
            node_ids.insert(node_id);
        }
    }
    node_ids
}

fn build_slice_selection(
    analysis: &AnalysisResult,
    ast_index: &AstSliceIndex,
    pdg_node_ids: &HashSet<usize>,
    target: &TargetSpec,
    policy: &HarnessPolicy,
    max_level: usize,
) -> SliceSelection {
    let mut selection = SliceSelection::default();
    selection.target_contract = target.contract.clone();
    selection.target_entry_function = target.entry_function.clone();
    selection.relevant_contracts.insert(target.contract.clone());
    if !target.focus_symbol.trim().is_empty() {
        selection
            .relevant_variables
            .insert(target.focus_symbol.clone());
    }

    if !target.entry_function.is_empty() {
        selection.add_contract_function(
            &target.contract,
            &target.entry_function,
            "Harness deps: target test entry",
        );
    }

    for node_id in pdg_node_ids {
        if let Some(node) = analysis.program_dependency_graph.nodes.get(node_id) {
            if let (Some(contract), Some(function)) =
                (&node.contract_context, &node.function_context)
            {
                if should_allow_harness_function(contract, function, target, &selection) {
                    selection.add_contract_function(
                        contract,
                        function,
                        "Harness deps: PDG node in target slice",
                    );
                }
            }
            if let Some(contract) = &node.contract_context {
                selection.relevant_contracts.insert(contract.clone());
            }
            match &node.kind {
                crate::analyzer::NodeKind::StorageRead(var)
                | crate::analyzer::NodeKind::StorageWrite(var)
                | crate::analyzer::NodeKind::VariableWrite(var) => {
                    selection.relevant_variables.insert(var.clone());
                }
                crate::analyzer::NodeKind::VariableRead => {
                    if let Some(var) = extract_variable_from_pdg_label(&node.label) {
                        selection.relevant_variables.insert(var);
                    }
                }
                crate::analyzer::NodeKind::ExternalCall
                | crate::analyzer::NodeKind::TaintSource => {
                    if let Some(receiver) = extract_receiver_variable(&node.label) {
                        selection.relevant_variables.insert(receiver.clone());
                        if let Some(contract_type) = ast_index.variable_types.get(&receiver) {
                            add_contract_dependency(
                                &mut selection,
                                contract_type.trim(),
                                target,
                                "Scenario deps: external receiver type used by target slice",
                            );
                        }
                    }
                }
                _ => {}
            }
        }
    }

    if policy.include_setup {
        for setup_function in ["setUp", "constructor"] {
            if analysis
                .contract_registry
                .function_map
                .get(&target.contract)
                .map_or(false, |functions| functions.contains_key(setup_function))
            {
                selection.add_contract_function(
                    &target.contract,
                    setup_function,
                    "Harness deps: target contract setup",
                );
            }
        }
    }

    if policy.include_same_contract_helpers || policy.include_inherited_helpers {
        expand_harness_call_closure(analysis, ast_index, target, policy, &mut selection);
    }

    if selection.has_target_entry() {
        for key in &selection.relevant_contract_functions {
            if let Some((contract, function)) = key.split_once("::") {
                selection.function_levels.insert(function.to_string(), 0);
                selection.contract_levels.insert(contract.to_string(), 0);
            }
        }
    } else {
        let (function_levels, contract_levels) =
            build_function_level_hierarchy(analysis, &selection.relevant_functions);
        selection.function_levels = function_levels;
        selection.contract_levels = contract_levels;
    }

    for (function, level) in &selection.function_levels {
        if *level <= max_level {
            selection.relevant_functions.insert(function.clone());
        }
    }

    for (contract, level) in &selection.contract_levels {
        if *level <= max_level {
            selection.relevant_contracts.insert(contract.clone());
        }
    }

    for (contract, variables) in &analysis.contract_registry.storage_map {
        if variables
            .keys()
            .any(|variable| selection.relevant_variables.contains(variable))
        {
            add_contract_dependency(
                &mut selection,
                contract,
                target,
                "Scenario deps: storage referenced by selected harness code",
            );
        }
    }

    collect_variables_for_selected_functions(analysis, ast_index, &mut selection);
    collect_qualified_definition_dependencies(ast_index, target, &mut selection);

    // NEW: Resolve missing dependencies based on text (e.g., Constants.MAX_TICK, Errors.InvalidTick)
    if policy.allow_text_dependency_expansion {
        let mut iteration = 0;
        loop {
            iteration += 1;
            // Temporarily render the current selection to text
            let temp_blocks = ast_index.render(&selection, true, false, max_level);
            let temp_text = temp_blocks.join("\n");

            let mut discovered_contracts = HashSet::new();
            for c in &ast_index.contracts {
                if !selection.relevant_contracts.contains(&c.name) {
                    let pattern = format!(r"\b{}\b", regex::escape(&c.name));
                    if let Ok(re) = regex::Regex::new(&pattern) {
                        if re.is_match(&temp_text) {
                            discovered_contracts.insert(c.name.clone());
                        }
                    }
                }
            }

            if discovered_contracts.is_empty() || iteration > 5 {
                break;
            }

            println!(
                "🔍 Discovered missing dependencies from text (iter {}): {:?}",
                iteration, discovered_contracts
            );

            for contract_name in &discovered_contracts {
                add_contract_dependency(
                    &mut selection,
                    contract_name,
                    target,
                    "Compiler-driven deps: referenced by rendered harness text",
                );
                if let Some(c) = ast_index
                    .contracts
                    .iter()
                    .find(|c| c.name == *contract_name)
                {
                    for item in &c.body_items {
                        if let Some(name) = &item.name {
                            if matches!(item.kind, AstContractItemKind::Function)
                                && should_allow_harness_function(
                                    contract_name,
                                    name,
                                    target,
                                    &selection,
                                )
                            {
                                selection.add_contract_function(
                                    contract_name,
                                    name,
                                    "Compiler-driven deps: function referenced by rendered harness text",
                                );
                            }
                            selection.relevant_variables.insert(name.clone());
                        }
                    }
                }
            }
        }
    }

    selection
}

fn expand_harness_call_closure(
    analysis: &AnalysisResult,
    ast_index: &AstSliceIndex,
    target: &TargetSpec,
    policy: &HarnessPolicy,
    selection: &mut SliceSelection,
) {
    use std::collections::VecDeque;

    let mut queue = VecDeque::new();
    let mut depth_by_key = HashMap::new();
    for key in selection.relevant_contract_functions.clone() {
        depth_by_key.insert(key.clone(), 0usize);
        queue.push_back(key);
    }

    while let Some(key) = queue.pop_front() {
        if selection.relevant_contract_functions.len() >= policy.max_harness_functions {
            println!(
                "⚠️  Harness budget reached: {} selected functions",
                policy.max_harness_functions
            );
            break;
        }

        let depth = *depth_by_key.get(&key).unwrap_or(&0);
        let Some((contract, function)) = key.split_once("::") else {
            continue;
        };
        if depth >= 8 {
            continue;
        }

        for (called_contract, called_function, reason) in
            find_called_contract_functions(analysis, ast_index, contract, function, policy)
        {
            if !should_allow_harness_function(&called_contract, &called_function, target, selection)
            {
                continue;
            }

            add_contract_dependency(selection, &called_contract, target, &reason);
            let inserted =
                selection.add_contract_function(&called_contract, &called_function, &reason);
            if inserted {
                let called_key =
                    SliceSelection::contract_function_key(&called_contract, &called_function);
                depth_by_key.insert(called_key.clone(), depth + 1);
                queue.push_back(called_key);
            }
        }
    }
}

fn add_contract_dependency(
    selection: &mut SliceSelection,
    contract: &str,
    target: &TargetSpec,
    reason: &str,
) {
    if contract.trim().is_empty() {
        return;
    }

    selection.relevant_contracts.insert(contract.to_string());
    selection
        .dependency_traces
        .entry(format!("contract::{}", contract))
        .or_insert_with(|| reason.to_string());

    if classify_harness_dependency(contract, target) == HarnessDependencyClass::Scenario {
        selection.full_contracts.insert(contract.to_string());
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum HarnessDependencyClass {
    Harness,
    Scenario,
    Protocol,
}

fn classify_harness_dependency(contract: &str, target: &TargetSpec) -> HarnessDependencyClass {
    if contract == target.contract {
        return HarnessDependencyClass::Harness;
    }

    let lower = contract.to_ascii_lowercase();
    if ["mock", "token", "oracle", "pool", "vault", "fixture"]
        .iter()
        .any(|needle| lower.contains(needle))
    {
        HarnessDependencyClass::Scenario
    } else {
        HarnessDependencyClass::Protocol
    }
}

fn should_allow_harness_function(
    contract: &str,
    function: &str,
    target: &TargetSpec,
    selection: &SliceSelection,
) -> bool {
    if target.entry_function.trim().is_empty() {
        return true;
    }

    if contract == target.contract {
        return function == target.entry_function
            || is_setup_function(function)
            || !is_test_like_function(function)
            || selection.contains_contract_function(contract, function);
    }

    if is_test_like_function(function) {
        return false;
    }

    if is_setup_function(function) {
        return selection.contains_contract_function(contract, function);
    }

    true
}

fn collect_qualified_definition_dependencies(
    ast_index: &AstSliceIndex,
    target: &TargetSpec,
    selection: &mut SliceSelection,
) {
    let known_defs: HashMap<String, ast::ContractKind> = ast_index
        .contracts
        .iter()
        .map(|contract| (contract.name.clone(), contract.kind))
        .collect();

    for _ in 0..5 {
        let mut discovered = Vec::new();

        for contract in &ast_index.contracts {
            let contract_selected = selection.relevant_contracts.contains(&contract.name)
                || selection.full_contracts.contains(&contract.name);
            if !contract_selected {
                continue;
            }

            for item in &contract.body_items {
                if should_exclude_harness_item(&contract.name, item, selection) {
                    continue;
                }
                if !(selection.full_contracts.contains(&contract.name)
                    || should_include_contract_item(&contract.name, item, selection, true))
                {
                    continue;
                }

                let mut referenced_defs = extract_qualified_definition_names(&item.code);
                referenced_defs.extend(extract_direct_definition_names(&item.code, &known_defs));

                for def_name in referenced_defs {
                    let Some(kind) = known_defs.get(&def_name).copied() else {
                        continue;
                    };
                    if selection.relevant_contracts.contains(&def_name) {
                        continue;
                    }
                    discovered.push((def_name, kind));
                }
            }
        }

        if discovered.is_empty() {
            break;
        }

        for (def_name, kind) in discovered {
            add_contract_dependency(
                selection,
                &def_name,
                target,
                "Protocol deps: qualified Definition.member reference",
            );
            if matches!(kind, ast::ContractKind::Library)
                || matches!(kind, ast::ContractKind::Interface)
                || classify_harness_dependency(&def_name, target)
                    == HarnessDependencyClass::Scenario
            {
                selection.full_contracts.insert(def_name);
            }
        }
    }
}

fn extract_qualified_definition_names(code: &str) -> HashSet<String> {
    let mut names = HashSet::new();
    let tokens = tokenize_code_for_qualified_refs(code);
    for window in tokens.windows(2) {
        if window[1] == "." && is_symbol_like_identifier(&window[0]) {
            names.insert(window[0].clone());
        }
    }
    names
}

fn extract_direct_definition_names(
    code: &str,
    known_defs: &HashMap<String, ast::ContractKind>,
) -> HashSet<String> {
    tokenize_code_for_qualified_refs(code)
        .into_iter()
        .filter(|token| is_symbol_like_identifier(token) && known_defs.contains_key(token))
        .collect()
}

fn tokenize_code_for_qualified_refs(code: &str) -> Vec<String> {
    let mut tokens = Vec::new();
    let mut current = String::new();
    for ch in code.chars() {
        if ch.is_ascii_alphanumeric() || ch == '_' {
            current.push(ch);
        } else {
            if !current.is_empty() {
                tokens.push(std::mem::take(&mut current));
            }
            if ch == '.' {
                tokens.push(ch.to_string());
            }
        }
    }
    if !current.is_empty() {
        tokens.push(current);
    }
    tokens
}

fn is_symbol_like_identifier(token: &str) -> bool {
    token
        .chars()
        .next()
        .map(|ch| ch.is_ascii_uppercase())
        .unwrap_or(false)
}

fn collect_variables_for_selected_functions(
    analysis: &AnalysisResult,
    ast_index: &AstSliceIndex,
    selection: &mut SliceSelection,
) {
    for node in analysis.program_dependency_graph.nodes.values() {
        let in_selected_function = match (&node.contract_context, &node.function_context) {
            (Some(contract), Some(function)) if selection.has_target_entry() => {
                selection.contains_contract_function(contract, function)
            }
            (_, Some(function)) => selection.relevant_functions.contains(function),
            _ => false,
        };

        if !in_selected_function {
            continue;
        }

        match &node.kind {
            crate::analyzer::NodeKind::StorageRead(var)
            | crate::analyzer::NodeKind::StorageWrite(var)
            | crate::analyzer::NodeKind::VariableWrite(var) => {
                selection.relevant_variables.insert(var.clone());
            }
            crate::analyzer::NodeKind::VariableRead => {
                if let Some(var) = extract_variable_from_pdg_label(&node.label) {
                    selection.relevant_variables.insert(var);
                }
            }
            crate::analyzer::NodeKind::ExternalCall | crate::analyzer::NodeKind::TaintSource => {
                if let Some(receiver) = extract_receiver_variable(&node.label) {
                    selection.relevant_variables.insert(receiver.clone());
                    if let Some(contract_type) = ast_index.variable_types.get(&receiver) {
                        let contract_type = contract_type.trim().to_string();
                        let target = TargetSpec {
                            contract: selection.target_contract.clone(),
                            entry_function: selection.target_entry_function.clone(),
                            focus_symbol: String::new(),
                        };
                        add_contract_dependency(
                            selection,
                            &contract_type,
                            &target,
                            "Scenario deps: external receiver used by selected harness code",
                        );
                    }
                }
            }
            _ => {}
        }
    }

    for (contract, variables) in &analysis.contract_registry.storage_map {
        if variables
            .keys()
            .any(|variable| selection.relevant_variables.contains(variable))
        {
            selection.relevant_contracts.insert(contract.clone());
        }
    }
}

fn extract_variable_from_pdg_label(label: &str) -> Option<String> {
    let candidate = label
        .strip_prefix("read state var ")
        .or_else(|| label.strip_prefix("read global "))
        .or_else(|| label.strip_prefix("read "))
        .or_else(|| {
            label
                .strip_prefix("storage: ")
                .and_then(|s| s.rsplit('.').next())
        })?;

    let name = candidate.trim();
    if name.is_empty() {
        None
    } else {
        Some(name.to_string())
    }
}

fn find_harness_seed_nodes(analysis: &AnalysisResult, target: &TargetSpec) -> Vec<usize> {
    if target.entry_function.is_empty() {
        return find_sink_nodes(analysis, &target.focus_symbol);
    }

    println!(
        "🔍 Looking for harness seed nodes in target function: {}.{}",
        target.contract, target.entry_function
    );

    let mut function_nodes = Vec::new();

    for node_index in analysis.program_dependency_graph.graph.node_indices() {
        let Some(&stored_node_id) = analysis
            .program_dependency_graph
            .graph
            .node_weight(node_index)
        else {
            continue;
        };
        let Some(node) = analysis.program_dependency_graph.nodes.get(&stored_node_id) else {
            continue;
        };
        let in_target_function = node.function_context.as_deref() == Some(&target.entry_function)
            && node.contract_context.as_deref() == Some(&target.contract);
        if !in_target_function {
            continue;
        }

        function_nodes.push(node_index.index());
    }

    println!(
        "📊 Harness seed: {} target-function nodes",
        function_nodes.len()
    );
    function_nodes
}

fn find_sink_nodes(analysis: &AnalysisResult, variable_name: &str) -> Vec<usize> {
    let mut sinks = Vec::new();
    println!(
        "🔍 Looking for StorageWrite/VariableWrite nodes for variable: {}",
        variable_name
    );

    // 遍历graph的节点索引，找到对应的存储节点或变量节点
    for node_index in analysis.program_dependency_graph.graph.node_indices() {
        if let Some(&stored_node_id) = analysis
            .program_dependency_graph
            .graph
            .node_weight(node_index)
        {
            if let Some(node) = analysis.program_dependency_graph.nodes.get(&stored_node_id) {
                // 1. 匹配变量写入
                if matches!(node.kind, crate::analyzer::NodeKind::StorageWrite(ref v) if v == variable_name)
                    || matches!(node.kind, crate::analyzer::NodeKind::VariableWrite(ref v) if v == variable_name)
                {
                    println!("✅ Found sink node {} (graph index {}) : kind={:?}, label='{}', function_context={:?}",
                        stored_node_id, node_index.index(), node.kind, node.label, node.function_context);
                    sinks.push(node_index.index()); // 返回graph节点索引
                }
                // 2. 匹配断言节点 (ConstraintNode) - 如果变量名是 "ASSERT" 或 "REQUIRE"
                else if (variable_name == "ASSERT" || variable_name == "REQUIRE")
                    && matches!(node.kind, crate::analyzer::NodeKind::ConstraintNode)
                {
                    println!(
                        "✅ Found assertion sink node {} (graph index {}) : kind={:?}, label='{}'",
                        stored_node_id,
                        node_index.index(),
                        node.kind,
                        node.label
                    );
                    sinks.push(node_index.index());
                }
            }
        }
    }

    println!("📊 Total sink nodes found: {}", sinks.len());
    sinks
}

async fn get_source_from_nodes<'a>(
    _slicer: &mut crate::semantic_slicer::SemanticSlicer<'a, PdgAdapter<'a>>,
    analysis: &AnalysisResult,
    ast_index: &AstSliceIndex,
    _source_code: &str,
    slice_nodes: &std::collections::HashSet<usize>,
    target: &TargetSpec,
    policy: &HarnessPolicy,
    _exclude_libs: bool,
    include_types: bool,
    max_level: usize,
    aggressive_cleanup: bool,
) -> Vec<String> {
    let pdg_node_ids = graph_indices_to_pdg_node_ids(analysis, slice_nodes);
    let selection = build_slice_selection(
        analysis,
        ast_index,
        &pdg_node_ids,
        target,
        policy,
        max_level,
    );
    log_pdg_node_ids(analysis, &pdg_node_ids, "semantic_render_pdg_node_ids");
    log_slice_selection(&selection, "semantic_render_selection");
    let ast_blocks = ast_index.render(&selection, include_types, _exclude_libs, max_level);
    execution_log::detail(
        "semantic_render_blocks",
        format!(
            "before_cleanup_blocks={} before_cleanup_lines={}",
            ast_blocks.len(),
            count_block_lines(&ast_blocks)
        ),
    );

    if !aggressive_cleanup {
        return ast_blocks;
    }

    execution_log::phase_start("aggressive_noise_reduction");
    println!("\n🚀 Starting Advanced Noise Reduction Pipeline...");
    let mut pipeline = NoiseReductionPipeline::default();
    let result = pipeline.reduce(ast_blocks);
    result.stats.print_summary();
    execution_log::phase_end(
        "aggressive_noise_reduction",
        format!(
            "after_blocks={} after_lines={}",
            result.code_blocks.len(),
            count_block_lines(&result.code_blocks)
        ),
    );
    result.code_blocks
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
        if !receiver.is_empty()
            && !receiver.starts_with("call")
            && !receiver.starts_with("Expr")
            && !receiver.contains('(')
        {
            return Some(receiver.to_string());
        }
    }

    None
}

// 🔥 标准库检测函数
fn is_standard_library_contract(contract_name: &str) -> bool {
    const STDLIB_CONTRACTS: &[&str] = &[
        // OpenZeppelin
        "Address",
        "SafeMath",
        "Math",
        "SignedMath",
        "Strings",
        "Arrays",
        "ECDSA",
        "ERC165",
        "ERC20",
        "ERC721",
        "ERC1155",
        "Ownable",
        "ReentrancyGuard",
        "Pausable",
        "AccessControl",
        // Forge Standard Library
        "Test",
        "Script",
        "Vm",
        "VmSafe",
        "console",
        "safeconsole",
        "StdAssertions",
        "StdCheats",
        "StdUtils",
        "StdInvariant",
        "StdError",
        "StdStorage",
        "StdStyle",
        "StdMath",
        "StdJson",
        "CommonBase",
        "ScriptBase",
        "TestBase",
        // Solmate
        "ERC20Minimal",
        "ERC721Minimal",
        "Auth",
        "Owned",
        "WETH",
        "SafeTransferLib",
        "FixedPointMathLib",
        "MerkleProofLib",
        // Common utilities (not business logic)
        "Create2",
        // Note: "Clone" is kept here so it doesn't fall into the missing_base_stubs path.
        // However, Clone's body IS emitted (see STDLIB_FULL_BODY_CONTRACTS below).
        "Clone",
        "Multicall",
        "TransientReentrancyGuard",
        "Clones",
        "Context",
        "Counters",
        "EnumerableSet",
        "EnumerableMap",
    ];

    // 精确匹配或前缀匹配
    STDLIB_CONTRACTS.iter().any(|&stdlib| {
        contract_name == stdlib || contract_name.starts_with(&format!("{}_", stdlib))
        // 处理 Math_0, Math_1 等
    })
}

fn is_stdlib_needing_full_body(contract_name: &str) -> bool {
    const STDLIB_FULL_BODY_CONTRACTS: &[&str] = &[
        // Provides inherited helper functions used by child contracts.
        "Clone",
    ];

    STDLIB_FULL_BODY_CONTRACTS.iter().any(|&stdlib| {
        contract_name == stdlib || contract_name.starts_with(&format!("{}_", stdlib))
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

/// 三层过滤结果
struct ThreeLayerFilterResult {
    blacklist: std::collections::HashSet<String>, // 第一层：静态黑名单（直接剔除）
    whitelist: std::collections::HashSet<String>, // 第二层：S1.2保护白名单（强制保留）
    graylist: std::collections::HashSet<String>,  // 第三层：语义灰名单（待LLM仲裁）
}

/// 第一层：静态黑名单过滤。
///
/// 保持核心路径通用：这里不按名称模式剔除合约。框架/标准库裁剪应由
/// framework profile 或后续编译诊断驱动，而不是写死在 slicer 正确性逻辑里。
fn apply_static_blacklist(_contract: &str) -> bool {
    false
}

/// 第二层：目标合约白名单（强制保留 - 防止LLM误删）
fn apply_target_whitelist(contract: &str, target_contract: &str) -> bool {
    contract == target_contract
}

/// 三层漏斗过滤：黑名单 → 白名单 → 灰名单
fn three_layer_filter(
    contracts: &std::collections::HashSet<String>,
    target_contract: &str,
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

        // 第二层：显式目标白名单检查
        if apply_target_whitelist(contract, target_contract) {
            println!("✅ Layer 2 Whitelist: {} (target contract)", contract);
            result.whitelist.insert(contract.clone());
            continue;
        }

        // 第三层：语义灰名单（待LLM仲裁）
        println!(
            "⚠️  Layer 3 Graylist: {} (pending LLM arbitration)",
            contract
        );
        result.graylist.insert(contract.clone());
    }

    println!("\n📊 Three-Layer Filter Summary:");
    println!("   Total contracts: {}", contracts.len());
    println!("   🚫 Blacklist (filtered): {}", result.blacklist.len());
    println!("   ✅ Whitelist (kept): {}", result.whitelist.len());
    println!("   ⚠️  Graylist (pending LLM): {}\n", result.graylist.len());

    result
}

// 🔥 从静态切片结果中提取合约和函数信息
// 注意：这里的文本解析是必要的，因为：
// 1. 输入是analyzer::get_source_slice的字符串输出（已经是文本格式）
// 2. 这是two-phase处理的Phase 1，用于快速过滤，避免LLM分析所有代码
// 3. 真正的AST验证在Phase 2（get_source_from_nodes）中完成
fn extract_contracts_and_functions(
    slice: &[String],
) -> (
    std::collections::HashSet<String>,
    std::collections::HashSet<String>,
) {
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
) -> (
    std::collections::HashMap<String, usize>,
    std::collections::HashMap<String, usize>,
) {
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
fn find_called_functions(analysis: &AnalysisResult, function_name: &str) -> Vec<String> {
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
                let is_known = analysis
                    .contract_registry
                    .function_map
                    .values()
                    .any(|funcs| funcs.contains_key(called_name));

                if is_known {
                    if !is_interface_function(analysis, called_name) && called_name != function_name
                    {
                        called_functions.insert(called_name.to_string());
                    }
                }
            }

            // Case 2: Internal calls (AST pattern matching)
            // 检查所有已知函数名
            for (func_name, _) in analysis
                .contract_registry
                .function_map
                .iter()
                .flat_map(|(_, funcs)| funcs.iter())
            {
                // 🔥 匹配PDG label中的函数调用模式:
                // 1. "kind: Ident(functionName)" - AST表达式调用
                // 2. "functionName(" - 简单函数调用
                let ident_pattern = format!("Ident({})", func_name);
                let call_pattern = format!("{}(", func_name);

                if label.contains(&ident_pattern) || label.contains(&call_pattern) {
                    // 🔥 过滤接口函数和自身
                    if !is_interface_function(analysis, func_name)
                        && func_name.as_str() != function_name
                    {
                        called_functions.insert(func_name.to_string());
                    }
                }
            }
        }
    }

    called_functions.into_iter().collect()
}

fn find_called_contract_functions(
    analysis: &AnalysisResult,
    ast_index: &AstSliceIndex,
    contract_name: &str,
    function_name: &str,
    policy: &HarnessPolicy,
) -> Vec<(String, String, String)> {
    let mut called = HashSet::new();
    let mut result = Vec::new();
    let mut candidate_contracts = vec![contract_name.to_string()];
    if policy.include_inherited_helpers {
        candidate_contracts.extend(ast_index.base_contracts(contract_name));
    }

    let same_contract_functions: HashSet<String> = candidate_contracts
        .iter()
        .filter_map(|contract| analysis.contract_registry.function_map.get(contract))
        .flat_map(|functions| functions.keys().cloned())
        .collect();

    for node in analysis.program_dependency_graph.nodes.values() {
        if node.function_context.as_deref() != Some(function_name)
            || node.contract_context.as_deref() != Some(contract_name)
        {
            continue;
        }

        for callee in &same_contract_functions {
            if callee == function_name {
                continue;
            }
            let ident_pattern = format!("Ident({})", callee);
            let call_pattern = format!("{}(", callee);
            if !(node.label.contains(&ident_pattern) || node.label.contains(&call_pattern)) {
                continue;
            }

            for candidate_contract in &candidate_contracts {
                if analysis
                    .contract_registry
                    .function_map
                    .get(candidate_contract)
                    .map_or(false, |functions| functions.contains_key(callee))
                {
                    let key = (candidate_contract.clone(), callee.clone());
                    if called.insert(key.clone()) {
                        result.push((
                            key.0,
                            key.1,
                            "Harness deps: direct/indirect helper call".to_string(),
                        ));
                    }
                    break;
                }
            }
        }

        if matches!(
            node.kind,
            crate::analyzer::NodeKind::ExternalCall | crate::analyzer::NodeKind::TaintSource
        ) {
            let Some(receiver) = extract_receiver_variable(&node.label) else {
                continue;
            };
            let Some(method) = extract_called_member_name(&node.label) else {
                continue;
            };
            let Some(receiver_type) = ast_index.variable_types.get(&receiver) else {
                continue;
            };
            let receiver_contract = receiver_type.trim().to_string();
            if analysis
                .contract_registry
                .function_map
                .get(&receiver_contract)
                .map_or(false, |functions| functions.contains_key(&method))
            {
                let key = (receiver_contract, method);
                if called.insert(key.clone()) {
                    result.push((
                        key.0,
                        key.1,
                        "Scenario deps: receiver.method() used by harness".to_string(),
                    ));
                }
            }
        }
    }

    result
}

fn extract_called_member_name(label: &str) -> Option<String> {
    let cleaned = label
        .strip_prefix("external:")
        .map(str::trim)
        .unwrap_or(label.trim());
    let (_, tail) = cleaned.rsplit_once('.')?;
    let name = tail
        .split(|ch: char| !(ch.is_ascii_alphanumeric() || ch == '_'))
        .next()
        .unwrap_or("")
        .trim();
    if name.is_empty() {
        None
    } else {
        Some(name.to_string())
    }
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
                    if relevant_contracts.contains(&target_contract)
                        && target_contract != contract_name
                    {
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
        } else if path.is_dir() {
            // Skip common non-source directories
            if !path.ends_with("node_modules")
                && !path.ends_with(".git")
                && !path.ends_with("target")
            {
                collect_sol_files_recursive(&path, files)?;
            }
        }
    }

    Ok(())
}
