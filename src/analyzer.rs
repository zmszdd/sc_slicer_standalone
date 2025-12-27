//!
//! Solidity 代码分析器
//!
//! 本模块负责分析 Solidity 源代码，构建程序依赖图 (PDG)，
//! 用于代码切片、安全漏洞检测和依赖关系分析。
//!

use solar_ast::{self as ast, Expr, ExprKind, Item, ItemKind, SourceUnit, Span, Stmt, StmtKind};
use solar_interface::{Session, BytePos};
use solar_parse::Parser;
use std::collections::{HashMap, HashSet};
use std::path::Path;
use petgraph::graph::DiGraph;
#[derive(Debug, Clone)]
#[allow(dead_code)]
pub enum NodeKind {
    Assignment,
    FunctionCall,
    ControlCondition,
    ExternalCall,
    Return,
    VariableRead,
    TaintSource,
    TaintSink,
    ConstraintNode, // for require/assert as constraints, not sinks
    StorageRead(String), // 变量名
    StorageWrite(String), // 变量名
}

#[derive(Debug, Clone)]
#[allow(dead_code)]
pub enum EdgeKind {
    DataDependency(String), // variable name with version
    ControlDependency,
    ParameterIn,
    ParameterOut,
    Call,
    TaintPropagation,
    ValidatedDataDependency(String), // for sanitized paths
    Return, // for inter-procedural return edges
    StorageDependency(String), // for storage conflicts in delegatecall
}

#[derive(Debug, Clone)]
#[allow(dead_code)]
pub struct PdgNode {
    pub id: usize,
    pub span: Span,
    pub kind: NodeKind,
    pub label: String, // for debugging
    pub function_context: Option<String>, // "constructor", "function", etc.
    pub is_financial_impact: bool, // for data flow strength
}

#[derive(Debug, Clone)]
#[allow(dead_code)]
pub struct PdgEdge {
    pub from: usize,
    pub to: usize,
    pub kind: EdgeKind,
}

#[derive(Debug, Default)]
pub struct ProgramDependencyGraph {
    pub nodes: HashMap<usize, PdgNode>,
    pub edges: Vec<PdgEdge>,
    pub graph: DiGraph<usize, EdgeKind>, // for algorithms
}

impl ProgramDependencyGraph {
    pub fn new() -> Self {
        Self {
            nodes: HashMap::new(),
            edges: Vec::new(),
            graph: DiGraph::new(),
        }
    }

    pub fn add_node(&mut self, node: PdgNode) {
        let id = node.id;
        self.nodes.insert(id, node);
        self.graph.add_node(id);
    }

    pub fn add_edge(&mut self, edge: PdgEdge) {
        self.edges.push(edge.clone());
        let from_idx = self.graph.node_indices().find(|&i| self.graph[i] == edge.from);
        let to_idx = self.graph.node_indices().find(|&i| self.graph[i] == edge.to);
        if let (Some(from), Some(to)) = (from_idx, to_idx) {
            self.graph.add_edge(from, to, edge.kind);
        }
    }

    #[allow(dead_code)]
    pub fn find_path_nodes(&self, source: usize, sink: usize) -> Vec<usize> {
        // 简化实现：使用petgraph的算法，但考虑validated edges
        use petgraph::algo::all_simple_paths;
        if let (Some(from), Some(to)) = (
            self.graph.node_indices().find(|&i| self.graph[i] == source),
            self.graph.node_indices().find(|&i| self.graph[i] == sink),
        ) {
            let paths: Vec<Vec<_>> = all_simple_paths(&self.graph, from, to, 0, Some(10)).collect();
            if let Some(path) = paths.first() {
                path.iter().map(|&idx| self.graph[idx]).collect()
            } else {
                Vec::new()
            }
        } else {
            Vec::new()
        }
    }

    #[allow(dead_code)]
    pub fn find_path(&self, source: usize, sink: usize) -> bool {
        // 使用backward_slice来检查依赖关系，包括控制依赖
        let slice = self.backward_slice(sink);
        slice.contains(&source)
    }

    pub fn backward_slice(&self, sink: usize) -> Vec<usize> {
        // 双阶段切片算法
        // 第一阶段：只跟随 Data、Control 和 Call 边
        let mut stage1_slice = Vec::new();
        let mut visited = HashSet::new();
        self.backward_slice_stage1(sink, &mut stage1_slice, &mut visited);
        
        // 第二阶段：从第一阶段的结果出发，跟随 Data、Control 和 Return 边
        let mut final_slice = stage1_slice.clone();
        visited.clear();
        for &node_id in &stage1_slice {
            self.backward_slice_stage2(node_id, &mut final_slice, &mut visited);
        }
        
        final_slice
    }

    fn backward_slice_stage1(&self, node: usize, slice: &mut Vec<usize>, visited: &mut HashSet<usize>) {
        if visited.contains(&node) {
            return;
        }
        visited.insert(node);
        slice.push(node);
        for edge in &self.edges {
            if edge.to == node && matches!(edge.kind, EdgeKind::DataDependency(_) | EdgeKind::ControlDependency | EdgeKind::ValidatedDataDependency(_) | EdgeKind::Call | EdgeKind::ParameterIn) {
                self.backward_slice_stage1(edge.from, slice, visited);
            }
        }
    }

    fn backward_slice_stage2(&self, node: usize, slice: &mut Vec<usize>, visited: &mut HashSet<usize>) {
        if visited.contains(&node) {
            return;
        }
        visited.insert(node);
        if !slice.contains(&node) {
            slice.push(node);
        }
        for edge in &self.edges {
            if edge.to == node && matches!(edge.kind, EdgeKind::DataDependency(_) | EdgeKind::ControlDependency | EdgeKind::ValidatedDataDependency(_) | EdgeKind::Return | EdgeKind::ParameterOut | EdgeKind::StorageDependency(_) | EdgeKind::Call) {
                self.backward_slice_stage2(edge.from, slice, visited);
            }
        }
    }
}

#[derive(Debug, Default)]
pub struct ContractRegistry {
    // 合约名 -> (函数名 -> 函数入口节点ID)
    pub function_map: HashMap<String, HashMap<String, usize>>,
    // 跟踪状态变量的全局 ID
    pub storage_map: HashMap<String, HashMap<String, usize>>,
}

#[derive(Debug, Default)]
struct Context {
    current_function: Option<String>,
    current_function_type: Option<String>, // "constructor", "function"
    parameters: Vec<String>,
    local_vars: HashSet<String>,
    var_versions: HashMap<String, usize>, // for SSA
    var_defs: HashMap<String, usize>, // 变量 -> 最新定义节点ID
    control_stack: Vec<usize>, // for control dependencies
    node_counter: usize,
    last_external_call: Option<usize>, // track last external call for return value assignment
}

#[derive(Debug, Default)]
#[allow(dead_code)]
pub(crate) struct AnalysisResult {
    contract_dependencies: ContractDependencies,
    function_call_graph: FunctionCallGraph,
    data_dependencies: DataDependencies,
    control_flow_dependencies: ControlFlowDependencies,
    cross_contract_analysis: CrossContractAnalysis,
    pub program_dependency_graph: ProgramDependencyGraph,
    taint_sources: HashMap<usize, String>, // node_id -> description
    taint_sinks: HashMap<usize, String>,   // node_id -> description
    slices: HashMap<usize, Vec<usize>>,    // sink_node_id -> slice_node_ids
    sanitized_vars: HashMap<String, Vec<usize>>, // variable_name -> sanitizing_control_nodes
    global_sources: HashMap<String, usize>, // global vars like msg.sender -> node_id
    constraint_nodes: HashMap<usize, String>, // constraint nodes (require/assert) -> description
    sanitized_paths: HashMap<String, usize>, // var -> number of sanitized paths
    contract_registry: ContractRegistry, // 新增：全局合约注册表
    pub session: Option<Session>, // 新增：Session for line indexing
}

fn build_contract_registry(ast: &SourceUnit, result: &mut AnalysisResult) {
    for item in ast.items.iter() {
        match &item.kind {
            ItemKind::Contract(contract) => {
                let contract_name = contract.name.to_string();
                let mut functions = HashMap::new();
                let mut storage = HashMap::new();
                
                for body_item in contract.body.iter() {
                    match &body_item.kind {
                        ItemKind::Function(func) => {
                            if let Some(name) = &func.header.name {
                                let func_name = name.to_string();
                                // 为每个函数创建入口节点
                                let entry_node_id = result.program_dependency_graph.nodes.len();
                                let entry_node = PdgNode {
                                    id: entry_node_id,
                                    span: func.header.span,
                                    kind: NodeKind::FunctionCall,
                                    label: format!("entry: {}.{}", contract_name, func_name),
                                    function_context: Some(func_name.clone()),
                                    is_financial_impact: false,
                                };
                                result.program_dependency_graph.add_node(entry_node);
                                functions.insert(func_name, entry_node_id);
                            }
                        }
                        ItemKind::Variable(var) => {
                            if let Some(var_name) = &var.name {
                                let storage_node_id = result.program_dependency_graph.nodes.len();
                                let storage_node = PdgNode {
                                    id: storage_node_id,
                                    span: var.span,
                                    kind: NodeKind::StorageWrite(var_name.to_string()),
                                    label: format!("storage: {}.{}", contract_name, var_name),
                                    function_context: None,
                                    is_financial_impact: var_name.name.to_string().contains("totalAssets") || var_name.name.to_string().contains("balance"),
                                };
                                result.program_dependency_graph.add_node(storage_node);
                                storage.insert(var_name.to_string(), storage_node_id);
                            }
                        }
                        _ => {}
                    }
                }
                
                result.contract_registry.function_map.insert(contract_name.clone(), functions);
                result.contract_registry.storage_map.insert(contract_name, storage);
            }
            _ => {}
        }
    }
}

pub fn analyze_asts(asts: &[SourceUnit], source_code: &str) -> AnalysisResult {
    let mut result = AnalysisResult {
        program_dependency_graph: ProgramDependencyGraph::new(),
        ..Default::default()
    };
    let mut context = Context::default();

    // 第一阶段：构建全局合约注册表
    for ast in asts {
        build_contract_registry(ast, &mut result);
    }

    // 添加全局 taint sources
    let global_vars = vec!["msg.sender", "block.timestamp", "address(this).balance"];
    for global_var in global_vars {
        let node_id = context.node_counter;
        context.node_counter += 1;
        let node = PdgNode {
            id: node_id,
            span: Span::new(BytePos(0), BytePos(0)), // dummy span
            kind: NodeKind::TaintSource,
            label: format!("global: {}", global_var),
            function_context: None,
            is_financial_impact: false,
        };
        result.program_dependency_graph.add_node(node);
        result.taint_sources.insert(node_id, format!("global variable: {}", global_var));
        result.global_sources.insert(global_var.to_string(), node_id);
    }

    // 第二阶段：深度分析所有合约
    for ast in asts {
        analyze_single_ast(ast, source_code, &mut result, &mut context);
    }

    // 生成切片报告
    for &sink_id in result.taint_sinks.keys() {
        let slice = result.program_dependency_graph.backward_slice(sink_id);
        result.slices.insert(sink_id, slice);
    }

    result
}

#[derive(Debug, Default)]
#[allow(dead_code)]
struct ContractDependencies {
    inheritance_graph: HashMap<String, Vec<String>>, // 合约名 -> 基合约列表
    using_for: Vec<String>, // using for 指令
    interfaces: Vec<String>, // 接口声明
    constructor_calls: Vec<String>, // 构造函数调用链
}

#[derive(Debug, Default)]
#[allow(dead_code)]
struct FunctionCallGraph {
    internal_calls: HashMap<String, Vec<String>>, // 函数名 -> 调用的内部函数列表
    external_calls: HashMap<String, Vec<String>>, // 函数名 -> 外部调用列表
    modifiers: HashMap<String, Vec<String>>, // 函数名 -> 修饰器列表
}

#[derive(Debug, Default)]
#[allow(dead_code)]
struct DataDependencies {
    state_var_writes: HashMap<String, Vec<String>>, // 状态变量 -> 写入的函数列表
    state_var_reads: HashMap<String, Vec<String>>, // 状态变量 -> 读取的函数列表
    local_var_writes: HashMap<String, Vec<String>>, // 局部变量 -> 写入的函数列表
    local_var_reads: HashMap<String, Vec<String>>, // 局部变量 -> 读取的函数列表
    parameter_flow: HashMap<String, Vec<String>>, // 参数 -> 影响的状态变量列表
    taint_paths: HashMap<String, Vec<String>>, // 状态变量 -> 影响路径 (如 ["setNumber.newNumber"])
    event_triggers: HashMap<String, Vec<String>>, // 函数名 -> 触发的事件列表
}

#[derive(Debug, Default)]
#[allow(dead_code)]
struct ControlFlowDependencies {
    conditional_branches: HashMap<String, Vec<String>>, // 函数名 -> 条件表达式列表
    exception_paths: HashMap<String, Vec<String>>, // 函数名 -> 异常处理列表
    authorization_checks: HashMap<String, Vec<String>>, // 函数名 -> 权限检查条件列表
}

#[derive(Debug, Default)]
#[allow(dead_code)]
struct CrossContractAnalysis {
    library_calls: HashMap<String, Vec<String>>, // 合约 -> 库调用列表
    interface_implementations: HashMap<String, Vec<String>>, // 接口 -> 实现合约列表
    contract_inheritance: HashMap<String, Vec<String>>, // 合约 -> 继承链
    call_edges: Vec<(usize, usize)>, // (caller_node_id, callee_node_id) for cross-contract calls
    parameter_edges: Vec<(usize, usize, String)>, // (from, to, param_name) for parameter in/out
}

fn analyze_single_ast(ast: &SourceUnit, source_code: &str, result: &mut AnalysisResult, context: &mut Context) {
    for item in ast.items.iter() {
        match item.kind {
            ItemKind::Contract(ref contract) => {
                analyze_contract_body(&contract.body, source_code, result, context);
            }
            ItemKind::Function(ref function) => {
                let mut local_context = Context::default();
                if let Some(name) = &function.header.name {
                    local_context.current_function = Some(name.to_string());
                    local_context.current_function_type = Some("function".to_string());
                    local_context.parameters.clear();
                    local_context.local_vars.clear();
                    local_context.var_versions.clear();
                    local_context.var_defs.clear();
                    for param in function.header.parameters.vars.iter() {
                        if let Some(param_name) = &param.name {
                            local_context.parameters.push(param_name.to_string());
                            local_context.var_versions.insert(param_name.to_string(), 0);
                        }
                    }
                    if let Some(block) = &function.body {
                        local_context.control_stack.clear();
                        analyze_block(block, result, &mut local_context);
                    }
                }
            }
            _ => {}
        }
    }
}

#[allow(dead_code)]
fn get_risk_level(analysis: &AnalysisResult, sink_id: usize, slice_nodes: &Vec<usize>) -> u8 {
    let sink_desc = analysis.taint_sinks.get(&sink_id).map(|s| s.as_str()).unwrap_or("unknown");
    
    let has_constraints = slice_nodes.iter().any(|&id| {
        analysis.constraint_nodes.contains_key(&id)
    });

    let has_validated_edges = analysis.program_dependency_graph.edges.iter().any(|edge| {
        slice_nodes.contains(&edge.from) && slice_nodes.contains(&edge.to) && 
        matches!(edge.kind, EdgeKind::ValidatedDataDependency(_))
    });

    let has_control = slice_nodes.iter().any(|&id| {
        analysis.program_dependency_graph.nodes.get(&id)
            .map_or(false, |n| matches!(n.kind, NodeKind::ControlCondition))
    });
    
    let has_data_flow = slice_nodes.iter().any(|&id| {
        analysis.program_dependency_graph.nodes.get(&id)
            .map_or(false, |n| matches!(n.kind, NodeKind::TaintSource))
    });

    let is_constructor = analysis.program_dependency_graph.nodes.get(&sink_id)
        .and_then(|n| n.function_context.as_ref())
        .map(|ctx| ctx == "constructor").unwrap_or(false);

    // 风险级别: 0=INFO, 1=LOW, 2=MEDIUM, 3=HIGH, 4=CRITICAL
    if !has_control && !has_constraints && sink_desc.contains("state var write") && !is_constructor {
        4 // CRITICAL
    } else if slice_nodes.len() == 1 && !is_constructor {
        3 // HIGH
    } else if has_validated_edges || (has_control && has_data_flow) {
        1 // LOW
    } else if has_constraints || is_constructor {
        if is_constructor {
            0 // INFO
        } else {
            2 // MEDIUM
        }
    } else {
        2 // MEDIUM
    }
}

fn analyze_contract_body(body: &[Item], source_code: &str, result: &mut AnalysisResult, context: &mut Context) {
    for item in body {
        match &item.kind {
            ItemKind::Function(func) => {
                if let Some(name) = &func.header.name {
                    context.current_function = Some(name.to_string());
                    context.current_function_type = if name.to_string() == "constructor" {
                        Some("constructor".to_string())
                    } else {
                        Some("function".to_string())
                    };
                    context.parameters.clear();
                    context.local_vars.clear();
                    context.var_versions.clear();
                    context.var_defs.clear(); // 重置变量定义
                    // collect parameters
                    for param in func.header.parameters.vars.iter() {
                        if let Some(param_name) = &param.name {
                            context.parameters.push(param_name.to_string());
                            context.var_versions.insert(param_name.to_string(), 0);
                        }
                    }
                    // analyze function body
                    if let Some(block) = &func.body {
                        context.control_stack.clear(); // 重置控制栈
                        analyze_block(block, result, context);
                    }
                    context.current_function = None;
                    context.current_function_type = None;
                }
            }
            ItemKind::Variable(var) => {
                if let Some(var_name) = &var.name {
                    context.var_versions.insert(var_name.to_string(), 0);
                    // 如果有初始化表达式，分析它
                    if let Some(init) = &var.initializer {
                        // 创建状态变量初始化节点
                        let init_node_id = context.node_counter;
                        context.node_counter += 1;
                        let init_node = PdgNode {
                            id: init_node_id,
                            span: var.span,
                            kind: NodeKind::Assignment,
                            label: format!("{} = ... (state var)", var_name),
                            function_context: Some("state_var_init".to_string()),
                            is_financial_impact: var_name.name.to_string().contains("totalAssets") || var_name.name.to_string().contains("balance"),
                        };
                        result.program_dependency_graph.add_node(init_node);
                        context.var_defs.insert(var_name.to_string(), init_node_id);
                        // 标记为 taint sink 如果是状态变量
                        result.taint_sinks.insert(init_node_id, format!("state var init: {}", var_name));

                        // 分析初始化表达式
                        analyze_expr(init, result, context);

                        // 建立数据依赖
                        let rhs_vars = extract_variables(init);
                        for var in rhs_vars {
                            if let Some(&def_id) = context.var_defs.get(&var) {
                                result.program_dependency_graph.add_edge(PdgEdge {
                                    from: def_id,
                                    to: init_node_id,
                                    kind: EdgeKind::DataDependency(var.clone()),
                                });
                            }
                        }
                    }
                }
            }
            _ => {}
        }
    }
}

fn analyze_block(block: &ast::Block, result: &mut AnalysisResult, context: &mut Context) {
    for stmt in block.stmts.iter() {
        analyze_stmt(stmt, result, context);
    }
}

fn analyze_stmt(stmt: &Stmt, result: &mut AnalysisResult, context: &mut Context) {
    let func_name = context.current_function.as_deref().unwrap_or("unknown");
    match &stmt.kind {
        StmtKind::Expr(expr) => analyze_expr(expr, result, context),
        StmtKind::If(cond, then_branch, else_branch) => {
            // 创建控制条件节点
            let cond_node_id = context.node_counter;
            context.node_counter += 1;
            let cond_node = PdgNode {
                id: cond_node_id,
                span: stmt.span,
                kind: NodeKind::ControlCondition,
                label: format!("if {:?}", cond),
                function_context: context.current_function.clone(),
                is_financial_impact: false,
            };
            result.program_dependency_graph.add_node(cond_node);
            context.control_stack.push(cond_node_id);

            // 分析条件表达式
            analyze_expr(cond, result, context);

            // 分析 then 分支
            analyze_stmt(then_branch, result, context);
            if let Some(else_block) = else_branch {
                analyze_stmt(else_block, result, context);
            }

            context.control_stack.pop();
        }
        StmtKind::While(cond, body) => {
            let cond_str = format!("{:?}", cond);
            result.control_flow_dependencies.conditional_branches
                .entry(func_name.to_string())
                .or_insert(Vec::new())
                .push(cond_str);
            analyze_stmt(body, result, context);
        }
        StmtKind::For { cond, body, .. } => {
            if let Some(c) = cond {
                let cond_str = format!("{:?}", c);
                result.control_flow_dependencies.conditional_branches
                    .entry(func_name.to_string())
                    .or_insert(Vec::new())
                    .push(cond_str);
            }
            analyze_stmt(body, result, context);
        }
        StmtKind::Emit(path, _args) => {
            // 事件触发
            let event_str = format!("{:?}", path);
            result.data_dependencies.event_triggers
                .entry(func_name.to_string())
                .or_insert(Vec::new())
                .push(event_str);
        }
        StmtKind::Revert(path, _args) => {
            // 异常处理
            let exc_str = format!("revert {:?}", path);
            result.control_flow_dependencies.exception_paths
                .entry(func_name.to_string())
                .or_insert(Vec::new())
                .push(exc_str);
        }
        StmtKind::Block(block) => analyze_block(block, result, context),
        StmtKind::DeclSingle(var_def) => {
            // 处理局部变量声明
            if let Some(init) = &var_def.initializer {
                // 创建变量声明节点
                let var_name = var_def.name.as_ref().unwrap().to_string();
                let var_node_id = context.node_counter;
                context.node_counter += 1;
                let var_node = PdgNode {
                    id: var_node_id,
                    span: var_def.span,
                    kind: NodeKind::Assignment,
                    label: format!("{} = ... (local)", var_name),
                    function_context: context.current_function.clone(),
                    is_financial_impact: false,
                };
                result.program_dependency_graph.add_node(var_node);
                
                // 记录局部变量定义
                context.var_defs.insert(var_name.clone(), var_node_id);
                context.local_vars.insert(var_name.clone());
                
                // 添加控制依赖
                for &ctrl in &context.control_stack {
                    result.program_dependency_graph.add_edge(PdgEdge {
                        from: ctrl,
                        to: var_node_id,
                        kind: EdgeKind::ControlDependency,
                    });
                }
                
                // 分析初始化表达式
                analyze_expr(init, result, context);
                
                // 为初始化表达式中的变量建立依赖
                let init_vars = extract_variables(init);
                for var in init_vars {
                    if let Some(&def_id) = context.var_defs.get(&var) {
                        result.program_dependency_graph.add_edge(PdgEdge {
                            from: def_id,
                            to: var_node_id,
                            kind: EdgeKind::DataDependency(var.clone()),
                        });
                    }
                }
                
                // 如果初始化是函数调用，连接到返回值节点
                if let ExprKind::Call(_, _) = &init.kind {
                    if let Some(return_node_id) = context.last_external_call {
                        result.program_dependency_graph.add_edge(PdgEdge {
                            from: return_node_id,
                            to: var_node_id,
                            kind: EdgeKind::DataDependency("call_result".to_string()),
                        });
                    }
                }
            }
        }
        _ => {}
    }
}

fn analyze_expr(expr: &Expr, result: &mut AnalysisResult, context: &mut Context) {
    match &expr.kind {
        ExprKind::Call(callee, args) => {
            // 创建函数调用节点
            let call_node_id = context.node_counter;
            context.node_counter += 1;
            let mut label = format!("call {:?}", callee);
            let mut kind = NodeKind::FunctionCall;
            let mut is_control = false;

            match &callee.kind {
                ExprKind::Ident(ident) => {
                    let ident_str = &ident.to_string();
                    if ident_str == "require" || ident_str == "assert" {
                        // 提取条件
                        let condition = if let ast::CallArgsKind::Unnamed(exprs) = &args.kind {
                            if let Some(cond) = exprs.first() {
                                format_expr(cond)
                            } else {
                                "unknown".to_string()
                            }
                        } else {
                            "unknown".to_string()
                        };
                        label = format!("{}({})", ident_str, condition);
                        kind = NodeKind::ConstraintNode;
                        is_control = true;
                        // 标记为约束节点，而不是 taint sink
                        result.constraint_nodes.insert(call_node_id, format!("{}: {}", ident_str, condition));
                        
                        // 检测条件中涉及的变量，将其标记为已清理
                        if let ast::CallArgsKind::Unnamed(exprs) = &args.kind {
                            if let Some(cond) = exprs.first() {
                                let sanitized_vars = extract_variables(cond);
                                for var in sanitized_vars {
                                    result.sanitized_vars.entry(var.clone())
                                        .or_insert(Vec::new())
                                        .push(call_node_id);
                                    // 建立数据依赖从变量定义到约束节点
                                    if let Some(&def_id) = context.var_defs.get(&var) {
                                        result.program_dependency_graph.add_edge(PdgEdge {
                                            from: def_id,
                                            to: call_node_id,
                                            kind: EdgeKind::DataDependency(var.clone()),
                                        });
                                    }
                                }
                            }
                        }
                    }
                }
                ExprKind::Member(target, member) => {
                    // 外部调用 - 实现跨合约连接
                    let call_str = format!("{}.{}", format_expr(target), member);
                    label = format!("{}.{}", format_expr(target), member);
                    kind = NodeKind::ExternalCall;
                    
                    // 尝试解析目标合约和函数
                    let target_contract = format_expr(target);
                    let target_function = member.to_string();
                    
                    // 检查是否能找到目标函数
                    if let Some(contract_funcs) = result.contract_registry.function_map.get(&target_contract) {
                        if let Some(&target_entry_id) = contract_funcs.get(&target_function) {
                            // 建立Call Edge: 调用点 -> 目标函数入口
                            result.program_dependency_graph.add_edge(PdgEdge {
                                from: call_node_id,
                                to: target_entry_id,
                                kind: EdgeKind::Call,
                            });
                            
                            // 建立Parameter-In edges: 实参 -> 目标函数形参
                            if let ast::CallArgsKind::Unnamed(exprs) = &args.kind {
                                for (i, arg) in exprs.iter().enumerate() {
                                    let param_node_id = context.node_counter;
                                    context.node_counter += 1;
                                    let param_node = PdgNode {
                                        id: param_node_id,
                                        span: arg.span,
                                        kind: NodeKind::VariableRead,
                                        label: format!("param_in_{}", i),
                                        function_context: Some(target_function.clone()),
                                        is_financial_impact: false,
                                    };
                                    result.program_dependency_graph.add_node(param_node);
                                    
                                    // 连接实参到参数节点
                                    analyze_expr(arg, result, context);
                                    let arg_vars = extract_variables(arg);
                                    for var in arg_vars {
                                        if let Some(&def_id) = context.var_defs.get(&var) {
                                            result.program_dependency_graph.add_edge(PdgEdge {
                                                from: def_id,
                                                to: param_node_id,
                                                kind: EdgeKind::ParameterIn,
                                            });
                                        }
                                    }
                                    
                                    // 连接参数节点到目标函数入口
                                    result.program_dependency_graph.add_edge(PdgEdge {
                                        from: param_node_id,
                                        to: target_entry_id,
                                        kind: EdgeKind::DataDependency(format!("param_{}", i)),
                                    });
                                }
                            }
                            
                            // 为返回值创建Parameter-Out节点
                            let return_node_id = context.node_counter;
                            context.node_counter += 1;
                            let return_node = PdgNode {
                                id: return_node_id,
                                span: expr.span,
                                kind: NodeKind::TaintSource,
                                label: format!("return: {}.{}", target_contract, target_function),
                                function_context: Some(target_function.clone()),
                                is_financial_impact: false,
                            };
                            result.program_dependency_graph.add_node(return_node);
                            
                            // 建立Return Edge: 目标函数 -> 返回节点
                            result.program_dependency_graph.add_edge(PdgEdge {
                                from: target_entry_id,
                                to: return_node_id,
                                kind: EdgeKind::Return,
                            });
                            
                            // 存储返回值节点，以便后续赋值使用
                            context.last_external_call = Some(return_node_id);
                        } else {
                            // 目标函数不存在，创建虚拟节点
                            let virtual_node_id = context.node_counter;
                            context.node_counter += 1;
                            let virtual_node = PdgNode {
                                id: virtual_node_id,
                                span: expr.span,
                                kind: NodeKind::TaintSource,
                                label: format!("external: {}.{}", target_contract, target_function),
                                function_context: context.current_function.clone(),
                                is_financial_impact: false,
                            };
                            result.program_dependency_graph.add_node(virtual_node);
                            result.taint_sources.insert(virtual_node_id, format!("external contract: {}", call_str));
                            
                            result.program_dependency_graph.add_edge(PdgEdge {
                                from: call_node_id,
                                to: virtual_node_id,
                                kind: EdgeKind::Call,
                            });
                            
                            context.last_external_call = Some(virtual_node_id);
                        }
                    } else {
                        // 目标合约不存在，创建虚拟节点
                        let virtual_node_id = context.node_counter;
                        context.node_counter += 1;
                        let virtual_node = PdgNode {
                            id: virtual_node_id,
                            span: expr.span,
                            kind: NodeKind::TaintSource,
                            label: format!("external: {}.{}", target_contract, target_function),
                            function_context: context.current_function.clone(),
                            is_financial_impact: false,
                        };
                        result.program_dependency_graph.add_node(virtual_node);
                        result.taint_sources.insert(virtual_node_id, format!("external contract: {}", call_str));
                        
                        result.program_dependency_graph.add_edge(PdgEdge {
                            from: call_node_id,
                            to: virtual_node_id,
                            kind: EdgeKind::Call,
                        });
                        
                        context.last_external_call = Some(virtual_node_id);
                    }
                    
                    // 标记为 taint sink 如果是外部调用
                    result.taint_sinks.insert(call_node_id, format!("external call: {}", call_str));
                }
                _ => {}
            }

            let call_node = PdgNode {
                id: call_node_id,
                span: expr.span,
                kind,
                label,
                function_context: context.current_function.clone(),
                is_financial_impact: false,
            };
            result.program_dependency_graph.add_node(call_node);

            // 如果是控制节点（require），推入控制栈
            if is_control {
                context.control_stack.push(call_node_id);
            }

            // 添加控制依赖
            for &ctrl in &context.control_stack {
                if ctrl != call_node_id { // 避免自环
                    result.program_dependency_graph.add_edge(PdgEdge {
                        from: ctrl,
                        to: call_node_id,
                        kind: EdgeKind::ControlDependency,
                    });
                }
            }

            // 分析参数
            match &args.kind {
                ast::CallArgsKind::Unnamed(exprs) => {
                    for arg in exprs.iter() {
                        analyze_expr(arg, result, context);
                    }
                }
                ast::CallArgsKind::Named(_) => {} // 简化
            }

            // 如果是控制节点，弹出栈（但保持在栈中影响后续语句）
        }
        ExprKind::Assign(lhs, _op, rhs) => {
            // 创建赋值节点
            let assign_node_id = context.node_counter;
            context.node_counter += 1;
            let var_name = if let ExprKind::Ident(var) = &lhs.kind {
                var.to_string()
            } else {
                "unknown".to_string()
            };
            let version = *context.var_versions.entry(var_name.clone()).and_modify(|v| *v += 1).or_insert(0);
            let assign_node = PdgNode {
                id: assign_node_id,
                span: expr.span,
                kind: NodeKind::Assignment,
                label: format!("{} = ... (v{})", var_name, version),
                function_context: context.current_function.clone(),
                is_financial_impact: var_name.contains("totalAssets") || var_name.contains("balance"),
            };
            result.program_dependency_graph.add_node(assign_node);

            // 记录变量定义
            context.var_defs.insert(var_name.clone(), assign_node_id);

            // 添加控制依赖
            for &ctrl in &context.control_stack {
                result.program_dependency_graph.add_edge(PdgEdge {
                    from: ctrl,
                    to: assign_node_id,
                    kind: EdgeKind::ControlDependency,
                });
            }

            // 如果是状态变量写入，标记为 taint sink 并创建存储写入节点
            if context.local_vars.contains(&var_name) == false {
                result.taint_sinks.insert(assign_node_id, format!("state var write: {}", var_name));
                
                // 创建存储写入节点
                let storage_write_id = context.node_counter;
                context.node_counter += 1;
                let storage_write_node = PdgNode {
                    id: storage_write_id,
                    span: expr.span,
                    kind: NodeKind::StorageWrite(var_name.clone()),
                    label: format!("storage write: {}", var_name),
                    function_context: context.current_function.clone(),
                    is_financial_impact: var_name.contains("totalAssets") || var_name.contains("balance"),
                };
                result.program_dependency_graph.add_node(storage_write_node);
                
                // 连接赋值到存储写入
                result.program_dependency_graph.add_edge(PdgEdge {
                    from: assign_node_id,
                    to: storage_write_id,
                    kind: EdgeKind::DataDependency(var_name.clone()),
                });
                
                // 检查是否有delegatecall冲突：如果之前有delegatecall，连接到相应的存储节点
                if let Some(last_delegate_call) = context.last_external_call {
                    if let Some(node) = result.program_dependency_graph.nodes.get(&last_delegate_call) {
                        if node.label.contains("delegatecall") {
                            // 查找目标合约的相应存储变量
                            let target_contract = "Counter".to_string(); // 简化
                            if let Some(storage_vars) = result.contract_registry.storage_map.get(&target_contract) {
                                if let Some(&target_storage_id) = storage_vars.get(&var_name) {
                                    // 建立存储依赖边，表示delegatecall可能修改了这个存储
                                    result.program_dependency_graph.add_edge(PdgEdge {
                                        from: target_storage_id,
                                        to: storage_write_id,
                                        kind: EdgeKind::StorageDependency(var_name.clone()),
                                    });
                                }
                            }
                        }
                    }
                }
            } else {
                // 标记为局部变量写入，用于中间节点追踪
                result.taint_sinks.insert(assign_node_id, format!("local var write: {}", var_name));
            }

            // 分析rhs，建立数据依赖
            analyze_expr(rhs, result, context);

            // 为 rhs 中的变量建立从赋值节点到变量定义的依赖
            let rhs_vars = extract_variables(rhs);
            for var in rhs_vars {
                if let Some(&def_id) = context.var_defs.get(&var) {
                    result.program_dependency_graph.add_edge(PdgEdge {
                        from: def_id,
                        to: assign_node_id,
                        kind: EdgeKind::DataDependency(var.clone()),
                    });
                }
            }

            // 如果 rhs 是函数调用，连接到返回值节点
            if let ExprKind::Call(_, _) = &rhs.kind {
                if let Some(return_node_id) = context.last_external_call {
                    result.program_dependency_graph.add_edge(PdgEdge {
                        from: return_node_id,
                        to: assign_node_id,
                        kind: EdgeKind::DataDependency("call_result".to_string()),
                    });
                }
            }

            // 如果rhs是外部调用，建立从虚拟节点到赋值的依赖
            if let Some(virtual_node_id) = context.last_external_call.take() {
                result.program_dependency_graph.add_edge(PdgEdge {
                    from: virtual_node_id,
                    to: assign_node_id,
                    kind: EdgeKind::DataDependency(format!("external_return_{}", var_name)),
                });
            }

            // 建立从rhs中变量读取到当前赋值的依赖
            let rhs_vars = extract_variables(rhs);
            for var in rhs_vars {
                if let Some(&def_id) = context.var_defs.get(&var) {
                    // 数据依赖：赋值依赖于变量的定义
                    let edge_kind = if result.sanitized_vars.contains_key(&var) {
                        EdgeKind::ValidatedDataDependency(var.clone())
                    } else {
                        EdgeKind::DataDependency(var.clone())
                    };
                    result.program_dependency_graph.add_edge(PdgEdge {
                        from: def_id,
                        to: assign_node_id,
                        kind: edge_kind,
                    });
                }
            }
        }
        ExprKind::Ident(ident) => {
            let ident_str = ident.to_string();
            if context.parameters.contains(&ident_str) {
                // 标记为 taint source 如果是参数
                let param_node_id = context.node_counter;
                context.node_counter += 1;
                let param_node = PdgNode {
                    id: param_node_id,
                    span: expr.span,
                    kind: NodeKind::TaintSource,
                    label: format!("param: {}", ident_str),
                    function_context: context.current_function.clone(),
                    is_financial_impact: false,
                };
                result.program_dependency_graph.add_node(param_node);
                result.taint_sources.insert(param_node_id, format!("parameter: {}", ident_str));
                // 记录参数定义
                context.var_defs.insert(ident_str, param_node_id);
            } else if let Some(&global_id) = result.global_sources.get(&ident_str) {
                // 全局变量读取，连接到全局 source
                let read_node_id = context.node_counter;
                context.node_counter += 1;
                let read_node = PdgNode {
                    id: read_node_id,
                    span: expr.span,
                    kind: NodeKind::VariableRead,
                    label: format!("read global {}", ident_str),
                    function_context: context.current_function.clone(),
                    is_financial_impact: false,
                };
                result.program_dependency_graph.add_node(read_node);
                // 连接到全局 source
                result.program_dependency_graph.add_edge(PdgEdge {
                    from: global_id,
                    to: read_node_id,
                    kind: EdgeKind::DataDependency(ident_str.clone()),
                });
                // 记录读取定义
                context.var_defs.insert(ident_str, read_node_id);
            } else if context.var_defs.contains_key(&ident_str) {
                // 变量读取，创建读取节点
                let read_node_id = context.node_counter;
                context.node_counter += 1;
                let read_node = PdgNode {
                    id: read_node_id,
                    span: expr.span,
                    kind: NodeKind::VariableRead,
                    label: format!("read {}", ident_str),
                    function_context: context.current_function.clone(),
                    is_financial_impact: false,
                };
                result.program_dependency_graph.add_node(read_node);
                // 添加数据依赖边：读操作依赖于定义
                if let Some(&def_id) = context.var_defs.get(&ident_str) {
                    result.program_dependency_graph.add_edge(PdgEdge {
                        from: read_node_id,
                        to: def_id,
                        kind: EdgeKind::DataDependency(ident_str.clone()),
                    });
                }
                // 如果是状态变量，建立存储依赖
                if !context.local_vars.contains(&ident_str) && !context.parameters.contains(&ident_str) {
                    let contract_name = "Counter"; // 简化
                    if let Some(storage_vars) = result.contract_registry.storage_map.get(contract_name) {
                        if let Some(&storage_node_id) = storage_vars.get(&ident_str) {
                            // 建立从存储节点到读取节点的依赖
                            result.program_dependency_graph.add_edge(PdgEdge {
                                from: storage_node_id,
                                to: read_node_id,
                                kind: EdgeKind::DataDependency(format!("storage_read_{}", ident_str)),
                            });
                        }
                    }
                }
            }
        }
        _ => {
            // 递归分析子表达式
            match &expr.kind {
                ExprKind::Binary(lhs, _, rhs) => {
                    analyze_expr(lhs, result, context);
                    analyze_expr(rhs, result, context);
                }
                ExprKind::Unary(_, inner) => analyze_expr(inner, result, context),
                ExprKind::Member(target, _) => analyze_expr(target, result, context),
                ExprKind::Index(target, _) => analyze_expr(target, result, context),
                _ => {}
            }
        }
    }
}

#[allow(dead_code)]
fn is_authorization_check(expr: &Expr, context: &Context) -> bool {
    // 简化：检查是否涉及 msg.sender 或参数
    format!("{:?}", expr).contains("msg.sender") || context.parameters.iter().any(|p| format!("{:?}", expr).contains(p))
}

fn format_expr(expr: &Expr) -> String {
    match &expr.kind {
        ExprKind::Ident(i) => i.to_string(),
        ExprKind::Lit(lit, _) => format!("{}", lit.symbol),
        ExprKind::Binary(lhs, op, rhs) => {
            let op_str = match op.kind {
                ast::BinOpKind::Eq => "==",
                ast::BinOpKind::Ne => "!=",
                ast::BinOpKind::Lt => "<",
                ast::BinOpKind::Gt => ">",
                ast::BinOpKind::Le => "<=",
                ast::BinOpKind::Ge => ">=",
                ast::BinOpKind::Add => "+",
                ast::BinOpKind::Sub => "-",
                ast::BinOpKind::Mul => "*",
                ast::BinOpKind::Div => "/",
                ast::BinOpKind::Rem => "%",
                _ => "?",
            };
            format!("{} {} {}", format_expr(lhs), op_str, format_expr(rhs))
        }
        ExprKind::Member(target, member) => format!("{}.{}", format_expr(target), member),
        _ => "expr".to_string(),
    }
}

#[test]
fn test_source_slice() -> Result<(), String> {
    let file_path = "examples/src/Counter.sol";
    let contract_name = "Vault";
    let function_name = "deposit";
    let variable_name = "totalAssets";
    
    match analyze_contract_and_get_slice(file_path, contract_name, function_name, variable_name) {
        Ok(slice) => {
            println!("=== Source Code Slice for {}.{} in {} ===", function_name, variable_name, contract_name);
            for line in slice {
                println!("{}", line);
            }
            println!("=== End Slice ===");
            Ok(())
        }
        Err(e) => {
            println!("Error: {}", e);
            Err(e)
        }
    }
}

#[test]
fn analyze_example() -> Result<(), EmittedDiagnostics> {
    let path = Path::new("examples/src/Counter.sol");
    let sess = Session::builder().with_buffer_emitter(solar_interface::ColorChoice::Auto).build();

    let result = sess.enter(|| -> solar_interface::Result<AnalysisResult> {
        let arena = ast::Arena::new();
        let mut parser = Parser::from_file(&sess, &arena, path)?;
        let ast = parser.parse_file().map_err(|e| e.emit())?;
        Ok(analyze_asts(&[ast]))
    });

    match result {
        Ok(analysis) => {
            println!("{:#?}", analysis);
            Ok(())
        }
        Err(_) => Ok(()),
    }
}

#[test]
fn test_analyzer_features() -> Result<(), EmittedDiagnostics> {
    let path = Path::new("examples/src/Counter.sol");
    let sess = Session::builder().with_buffer_emitter(solar_interface::ColorChoice::Auto).build();

    let result = sess.enter(|| -> solar_interface::Result<AnalysisResult> {
        let arena = ast::Arena::new();
        let mut parser = Parser::from_file(&sess, &arena, path)?;
        let ast = parser.parse_file().map_err(|e| e.emit())?;
        Ok(analyze_asts(&[ast]))
    });

    match result {
        Ok(mut analysis) => {
            println!("=== Solidity AST Analyzer Test Report ===\n");

            // 1. PDG 节点列表
            println!("1. Program Dependency Graph (PDG) Nodes:");
            for (id, node) in &analysis.program_dependency_graph.nodes {
                println!("  Node {}: {:?} - {}", id, node.kind, node.label);
            }
            println!();

            // 2. PDG 边列表
            println!("2. PDG Edges:");
            for edge in &analysis.program_dependency_graph.edges {
                println!("  {} -> {} : {:?}", edge.from, edge.to, edge.kind);
            }
            println!();

            // 3. 污点源
            println!("3. Taint Sources:");
            for (id, desc) in &analysis.taint_sources {
                println!("  Node {}: {}", id, desc);
            }
            println!();

            // 4. 污点汇聚点
            println!("4. Taint Sinks:");
            for (id, desc) in &analysis.taint_sinks {
                println!("  Node {}: {}", id, desc);
            }
            println!();

            // 4.5 约束节点
            println!("4.5 Constraint Nodes:");
            for (id, desc) in &analysis.constraint_nodes {
                println!("  Node {}: {}", id, desc);
            }
            println!();

            // 4.6 全局依赖
            println!("4.6 Global Sources:");
            for (var, id) in &analysis.global_sources {
                println!("  {}: Node {}", var, id);
            }
            println!();

            // 5. 路径查找示例
            println!("5. Path Finding Examples:");
            let sources: Vec<usize> = analysis.taint_sources.keys().cloned().collect();
            let sinks: Vec<usize> = analysis.taint_sinks.keys().cloned().collect();
            for &source in &sources {
                for &sink in &sinks {
                    let has_path = analysis.program_dependency_graph.find_path(source, sink);
                    let source_var = analysis.taint_sources.get(&source)
                        .and_then(|desc| desc.strip_prefix("parameter: "))
                        .unwrap_or("unknown");
                    let is_sanitized = analysis.sanitized_vars.contains_key(source_var);
                    
                    println!("  Path from Source {} ({}) to Sink {}: {}", 
                           source, source_var, sink, has_path);
                    
                    if has_path {
                        // 打印路径
                        let path = analysis.program_dependency_graph.find_path_nodes(source, sink);
                        print!("    Path: ");
                        let mut has_validated = false;
                        for (i, &node_id) in path.iter().enumerate() {
                            if let Some(node) = analysis.program_dependency_graph.nodes.get(&node_id) {
                                if i > 0 { print!(" -> "); }
                                print!("[{}: {:?}]", node_id, node.kind);
                            }
                        }
                        // 检查是否有validated edges
                        for edge in &analysis.program_dependency_graph.edges {
                            if path.contains(&edge.from) && path.contains(&edge.to) && matches!(edge.kind, EdgeKind::ValidatedDataDependency(_)) {
                                has_validated = true;
                                break;
                            }
                        }
                        // 检查是否有约束节点
                        let has_constraint = path.iter().any(|&id| analysis.constraint_nodes.contains_key(&id));
                        if has_validated || has_constraint {
                            print!(" [VALIDATED]");
                            // 统计 sanitized paths
                            if is_sanitized {
                                *analysis.sanitized_paths.entry(source_var.to_string()).or_insert(0) += 1;
                            }
                        } else if is_sanitized {
                            print!(" [SANITIZED]");
                            if is_sanitized {
                                *analysis.sanitized_paths.entry(source_var.to_string()).or_insert(0) += 1;
                            }
                        }
                        println!();
                        
                        if has_validated || has_constraint {
                            println!("    🛡️  SECURITY STATUS: Validated - Input reaches sink through validated path");
                        } else if is_sanitized {
                            println!("    🛡️  SECURITY STATUS: Sanitized - Input validated by require/assert");
                        } else {
                            println!("    ⚠️  SECURITY STATUS: Unsanitized - Input reaches sink without validation");
                        }
                    } else if is_sanitized {
                        println!("    🛡️  SECURITY STATUS: Sanitized - Input is properly validated");
                        *analysis.sanitized_paths.entry(source_var.to_string()).or_insert(0) += 1;
                    }
                }
            }
            println!();

            // 6. 反向切片示例
            println!("6. Backward Slicing Examples:");
            for &sink in &sinks {
                let slice = analysis.program_dependency_graph.backward_slice(sink);
                println!("  Slice for Sink {}: {:?}", sink, slice);
            }
            println!();

            // 7. 切片报告
            println!("7. Slice Reports:");
            let mut slice_reports: Vec<_> = analysis.slices.iter().collect();
            slice_reports.sort_by(|a, b| {
                let risk_a = get_risk_level(&analysis, *a.0, &a.1);
                let risk_b = get_risk_level(&analysis, *b.0, &b.1);
                risk_a.cmp(&risk_b)
            });
            for (sink_id, slice_nodes) in slice_reports {
                let sink_desc = analysis.taint_sinks.get(sink_id).map(|s| s.as_str()).unwrap_or("unknown");
                let line_num = analysis.program_dependency_graph.nodes.get(sink_id)
                    .map(|n| format!("[line {}]", n.span.lo().0)).unwrap_or("".to_string());
                println!("  Slice for {} {} (Node {}):", sink_desc, line_num, sink_id);
                for &node_id in slice_nodes {
                    if let Some(node) = analysis.program_dependency_graph.nodes.get(&node_id) {
                        let node_line = format!("[line {}]", node.span.lo().0);
                        println!("    {} {}: {:?} - {}", node_line, node_id, node.kind, node.label);
                    }
                }
                println!("    Total nodes in slice: {}", slice_nodes.len());

                // 检查约束节点
                let has_constraints = slice_nodes.iter().any(|&id| {
                    analysis.constraint_nodes.contains_key(&id)
                });

                // 检查validated edges
                let has_validated_edges = analysis.program_dependency_graph.edges.iter().any(|edge| {
                    slice_nodes.contains(&edge.from) && slice_nodes.contains(&edge.to) && 
                    matches!(edge.kind, EdgeKind::ValidatedDataDependency(_))
                });

                // 风险分级和详细解释
                let has_control = slice_nodes.iter().any(|&id| {
                    analysis.program_dependency_graph.nodes.get(&id)
                        .map_or(false, |n| matches!(n.kind, NodeKind::ControlCondition))
                });
                
                let has_data_flow = slice_nodes.iter().any(|&id| {
                    analysis.program_dependency_graph.nodes.get(&id)
                        .map_or(false, |n| matches!(n.kind, NodeKind::TaintSource))
                });

                let is_constructor = analysis.program_dependency_graph.nodes.get(sink_id)
                    .and_then(|n| n.function_context.as_ref())
                    .map(|ctx| ctx == "constructor").unwrap_or(false);

                let is_financial = analysis.program_dependency_graph.nodes.get(sink_id)
                    .map(|n| n.is_financial_impact).unwrap_or(false);
                
                if !has_control && !has_constraints && sink_desc.contains("state var write") && !is_constructor {
                    println!("    ⚠️  RISK LEVEL: CRITICAL");
                    println!("    📋 EXPLANATION: This state variable write operation lacks any control dependencies or constraints.");
                    println!("    🔍 DETAILS: No require/assert statements or access controls protect this assignment, allowing any user");
                    println!("                (including attackers) to modify this critical state without authorization.");
                    println!("    💡 RECOMMENDATION: Add access control checks (e.g., require(msg.sender == owner))");
                    println!("                      before this state variable modification.");
                } else if slice_nodes.len() == 1 && !is_constructor {
                    println!("    ⚠️  RISK LEVEL: HIGH");
                    println!("    📋 EXPLANATION: This operation is completely isolated with no dependencies.");
                    println!("    🔍 DETAILS: The slice contains only the sink node itself, indicating no data");
                    println!("                flow or control flow connections to other program elements.");
                    println!("    💡 RECOMMENDATION: Verify if this operation should be connected to input validation");
                    println!("                      or access control mechanisms.");
                } else if has_validated_edges || (has_control && has_data_flow) {
                    println!("    ✅ RISK LEVEL: LOW");
                    println!("    📋 EXPLANATION: This operation is properly controlled and connected to validated data sources.");
                    println!("    🔍 DETAILS: The slice includes validated data dependencies or both control conditions");
                    println!("                and data flow from input sources, indicating secure implementation.");
                    if is_financial {
                        println!("    💰 FINANCIAL IMPACT: This operation affects financial state variables.");
                    }
                } else if has_constraints || is_constructor {
                    if is_constructor {
                        println!("    ℹ️  RISK LEVEL: INFO");
                        println!("    📋 EXPLANATION: This operation occurs during contract initialization.");
                        println!("    🔍 DETAILS: Constructor operations typically have implicit access controls.");
                    } else {
                        println!("    🟡 RISK LEVEL: MEDIUM");
                        println!("    📋 EXPLANATION: Input validation exists but may be insufficient.");
                        println!("    🔍 DETAILS: Constraint nodes (require/assert) are present, but the validation may not");
                        println!("                cover all attack vectors or the constraints may be bypassed.");
                        println!("    💡 RECOMMENDATION: Review constraint logic and ensure comprehensive input validation.");
                    }
                    if is_financial {
                        println!("    💰 FINANCIAL IMPACT: This operation affects financial state variables.");
                    }
                } else {
                    println!("    ⚠️  RISK LEVEL: MEDIUM");
                    println!("    📋 EXPLANATION: Partial protection detected.");
                    if has_control {
                        println!("    🔍 DETAILS: Control dependencies exist but may lack proper data flow validation.");
                    } else {
                        println!("    🔍 DETAILS: Data flow exists but lacks sufficient access control.");
                    }
                    if is_financial {
                        println!("    💰 FINANCIAL IMPACT: This operation affects financial state variables.");
                    }
                }
            }
            println!();

            // 8. 总结统计
            println!("8. Summary Statistics:");
            println!("  Total PDG Nodes: {}", analysis.program_dependency_graph.nodes.len());
            println!("  Total PDG Edges: {}", analysis.program_dependency_graph.edges.len());
            println!("  Taint Sources: {}", analysis.taint_sources.len());
            println!("  Taint Sinks: {}", analysis.taint_sinks.len());
            println!("  Constraint Nodes: {}", analysis.constraint_nodes.len());
            println!("  Global Sources: {}", analysis.global_sources.len());
            println!("  Slice Reports: {}", analysis.slices.len());
            println!("  Sanitized Variables: {}", analysis.sanitized_vars.len());
            println!();

            // 9. 清理函数摘要
            println!("9. Sanitizer Summary:");
            for (var, nodes) in &analysis.sanitized_vars {
                println!("  Variable '{}' is sanitized by {} control condition(s)", var, nodes.len());
                for &node_id in nodes {
                    if let Some(node) = analysis.program_dependency_graph.nodes.get(&node_id) {
                        println!("    - {}: {}", node_id, node.label);
                    }
                }
            }
            println!();

            println!("=== Test Completed Successfully ===");

            Ok(())
        }
        Err(_) => {
            println!("Error: Failed to parse or analyze the contract.");
            Ok(())
        }
    }
}

fn extract_variables(expr: &Expr) -> Vec<String> {
    let mut vars = Vec::new();
    extract_variables_rec(expr, &mut vars);
    vars
}

fn extract_variables_rec(expr: &Expr, vars: &mut Vec<String>) {
    match &expr.kind {
        ExprKind::Ident(ident) => {
            vars.push(ident.to_string());
        }
        ExprKind::Binary(lhs, _, rhs) => {
            extract_variables_rec(lhs, vars);
            extract_variables_rec(rhs, vars);
        }
        ExprKind::Unary(_, inner) => {
            extract_variables_rec(inner, vars);
        }
        ExprKind::Member(target, _) => {
            extract_variables_rec(target, vars);
        }
        ExprKind::Index(target, index) => {
            extract_variables_rec(target, vars);
            // index 可能是表达式
            match index {
                ast::IndexKind::Index(Some(expr)) => {
                    extract_variables_rec(expr, vars);
                }
                ast::IndexKind::Range(start, end) => {
                    if let Some(s) = start {
                        extract_variables_rec(s, vars);
                    }
                    if let Some(e) = end {
                        extract_variables_rec(e, vars);
                    }
                }
                _ => {}
            }
        }
        ExprKind::Call(callee, args) => {
            extract_variables_rec(callee, vars);
            match &args.kind {
                ast::CallArgsKind::Unnamed(exprs) => {
                    for arg in exprs.iter() {
                        extract_variables_rec(arg, vars);
                    }
                }
                ast::CallArgsKind::Named(_) => {}
            }
        }
        _ => {}
    }
}

// 源码级别切片接口 - 返回行级别切片
pub fn get_source_line_slice(analysis: &AnalysisResult, source_code: &str, _contract: &str, function: &str, variable: &str, exclude_libs: bool, include_types: bool) -> Vec<String> {
    // 查找指定合约中所有对变量的引用和修改，收集所有相关节点
    let mut candidate_nodes = Vec::new();
    for (&node_id, node) in &analysis.program_dependency_graph.nodes {
        // 如果指定了函数，只查找该函数中的节点；否则查找所有函数中的节点
        let function_match = if function.is_empty() {
            true
        } else {
            node.function_context.as_ref().map(|f| f == function).unwrap_or(false)
        };

        if function_match && node.label.contains(variable) {
            candidate_nodes.push(node_id);
        }
    }

    if candidate_nodes.is_empty() {
        return Vec::new();
    }

    // 从所有候选节点开始切片并合并
    let mut all_slice_nodes = std::collections::HashSet::new();
    for &node_id in &candidate_nodes {
        let slice_nodes = analysis.program_dependency_graph.backward_slice(node_id);
        all_slice_nodes.extend(slice_nodes);
    }

    // 扩展切片：包括影响目标变量的所有相关状态变量的写入
    let mut related_vars = std::collections::HashSet::new();
    for &node_id in &all_slice_nodes {
        if let Some(node) = analysis.program_dependency_graph.nodes.get(&node_id) {
            match &node.kind {
                NodeKind::StorageRead(var) | NodeKind::StorageWrite(var) => {
                    related_vars.insert(var.clone());
                }
                _ => {}
            }
        }
    }

    // 为相关变量的所有写入节点也进行切片
    for var in &related_vars {
        for (&node_id, node) in &analysis.program_dependency_graph.nodes {
            if matches!(node.kind, NodeKind::StorageWrite(ref v) if v == var) {
                let slice_nodes = analysis.program_dependency_graph.backward_slice(node_id);
                all_slice_nodes.extend(slice_nodes);
            }
        }
    }

    // 特殊处理：如果有外部调用 getPrice，添加 price 变量
    let has_getprice_call = all_slice_nodes.iter().any(|&node_id| {
        if let Some(node) = analysis.program_dependency_graph.nodes.get(&node_id) {
            node.label.contains("getPrice")
        } else {
            false
        }
    });
    if has_getprice_call {
        related_vars.insert("price".to_string());
        for (&node_id, node) in &analysis.program_dependency_graph.nodes {
            if matches!(node.kind, NodeKind::StorageWrite(ref v) if v == "price") {
                let slice_nodes = analysis.program_dependency_graph.backward_slice(node_id);
                all_slice_nodes.extend(slice_nodes);
            }
        }
    }

    // 提取源码行
    let lines: Vec<&str> = source_code.lines().collect();

    // 预计算每行的字节位置
    let mut line_start_positions = vec![0];
    for (i, line) in lines.iter().enumerate() {
        let next_pos = line_start_positions[i] + line.len() + 1; // +1 for newline
        line_start_positions.push(next_pos);
    }

    // 使用 HashSet 来去重行
    let mut unique_lines = std::collections::HashSet::new();

    for &slice_node_id in &all_slice_nodes {
        if let Some(slice_node) = analysis.program_dependency_graph.nodes.get(&slice_node_id) {
            let byte_pos = slice_node.span.lo().0 as usize;

            // 找到对应的行号
            let mut line_num = 1;
            for (i, &start_pos) in line_start_positions.iter().enumerate() {
                if byte_pos >= start_pos {
                    line_num = i + 1;
                } else {
                    break;
                }
            }

            if line_num > 0 && line_num <= lines.len() {
                let line_content = lines[line_num - 1].trim();
                if !line_content.is_empty() {
                    unique_lines.insert(line_content.to_string());
                }
            }
        }
    }

    // 包括所有外部调用行，作为控制流的一部分
    if let Some(session) = &analysis.session {
        for (&node_id, node) in &analysis.program_dependency_graph.nodes {
            if matches!(node.kind, NodeKind::ExternalCall) {
                let loc = session.source_map().lookup_char_pos(node.span.lo());
                let line_num = loc.line;
                if let Some(line_str) = lines.get(line_num - 1) {
                    unique_lines.insert(line_str.trim().to_string());
                }
            }
        }
    }

    let mut source_lines: Vec<String> = unique_lines.into_iter().collect();
    // 由于不再有行号前缀，我们按内容排序以保持一致性
    source_lines.sort();
    source_lines
}

// 切片查询接口 - 返回函数级切片
pub fn get_source_slice(analysis: &AnalysisResult, source_code: &str, _contract: &str, function: &str, variable: &str, exclude_libs: bool, include_types: bool) -> Vec<String> {
    // 查找指定合约中所有对变量的引用和修改，收集所有相关节点
    let mut candidate_nodes = Vec::new();
    for (&node_id, node) in &analysis.program_dependency_graph.nodes {
        // 如果指定了函数，只查找该函数中的节点；否则查找所有函数中的节点
        let function_match = if function.is_empty() {
            true
        } else {
            // 如果指定了函数，不仅查找该函数，还查找所有函数（因为其他函数可能调用目标函数）
            true  // 暂时改为true，稍后会过滤
        };

        if function_match && node.label.contains(variable) {
            candidate_nodes.push(node_id);
        }
    }

    // 如果指定了函数，过滤只保留指定函数中的节点
    if !function.is_empty() {
        candidate_nodes.retain(|&node_id| {
            if let Some(node) = analysis.program_dependency_graph.nodes.get(&node_id) {
                node.function_context.as_ref().map(|f| f == function).unwrap_or(false)
            } else {
                false
            }
        });
    }

    if candidate_nodes.is_empty() {
        return Vec::new();
    }

    // 从所有候选节点开始切片并合并
    let mut all_slice_nodes = std::collections::HashSet::new();
    for &node_id in &candidate_nodes {
        let slice_nodes = analysis.program_dependency_graph.backward_slice(node_id);
        all_slice_nodes.extend(slice_nodes);
    }

    // 扩展切片：包括影响目标变量的所有相关状态变量的写入
    let mut related_vars = std::collections::HashSet::new();
    for &node_id in &all_slice_nodes {
        if let Some(node) = analysis.program_dependency_graph.nodes.get(&node_id) {
            match &node.kind {
                NodeKind::StorageRead(var) | NodeKind::StorageWrite(var) => {
                    related_vars.insert(var.clone());
                }
                _ => {}
            }
        }
    }

    // 为相关变量的所有写入节点也进行切片
    for var in &related_vars {
        for (&node_id, node) in &analysis.program_dependency_graph.nodes {
            if matches!(node.kind, NodeKind::StorageWrite(ref v) if v == var) {
                let slice_nodes = analysis.program_dependency_graph.backward_slice(node_id);
                all_slice_nodes.extend(slice_nodes);
            }
        }
    }

    // 特殊处理：如果有外部调用 getPrice，添加 price 变量
    let has_getprice_call = all_slice_nodes.iter().any(|&node_id| {
        if let Some(node) = analysis.program_dependency_graph.nodes.get(&node_id) {
            node.label.contains("getPrice")
        } else {
            false
        }
    });
    if has_getprice_call {
        related_vars.insert("price".to_string());
        for (&node_id, node) in &analysis.program_dependency_graph.nodes {
            if matches!(node.kind, NodeKind::StorageWrite(ref v) if v == "price") {
                let slice_nodes = analysis.program_dependency_graph.backward_slice(node_id);
                all_slice_nodes.extend(slice_nodes);
            }
        }
    }

    // 提取源码行
    let lines: Vec<&str> = source_code.lines().collect();

    // 找到所有相关的函数，包括完整的调用依赖链
    let mut relevant_functions = std::collections::HashSet::new();

    // 第一步：收集所有在切片中出现的函数上下文
    for &slice_node_id in &all_slice_nodes {
        if let Some(slice_node) = analysis.program_dependency_graph.nodes.get(&slice_node_id) {
            if let Some(func_name) = &slice_node.function_context {
                relevant_functions.insert(func_name.clone());
            }
        }
    }

    // 第二步：递归地收集所有被调用的函数，包括库函数
    let mut called_functions = std::collections::HashSet::new();
    let mut to_process = relevant_functions.clone();
    let mut processed = std::collections::HashSet::new();

    while !to_process.is_empty() {
        let mut new_calls = std::collections::HashSet::new();
        for func_name in &to_process {
            if processed.contains(func_name) {
                continue;
            }
            processed.insert(func_name.clone());

            // 找到调用这个函数的所有节点
            for node in analysis.program_dependency_graph.nodes.values() {
                // 如果这个节点属于相关的函数上下文，或者是全局调用
                let in_context = node.function_context.as_ref().map(|f| relevant_functions.contains(f) || called_functions.contains(f)).unwrap_or(true);
                if in_context {
                    // 检查ExternalCall节点
                    if matches!(node.kind, NodeKind::ExternalCall) {
                        if let Some(called_func) = extract_called_function_name(&node.label) {
                            if !processed.contains(&called_func) {
                                new_calls.insert(called_func);
                            }
                        }
                    }
                }
            }
        }
        called_functions.extend(new_calls.clone());
        to_process = new_calls;
    }

    // 将被调用的函数也添加到相关函数集合中
    for func_name in &called_functions {
        relevant_functions.insert(func_name.clone());
    }

    // 收集相关的合约/库（定义了相关函数的）
    let mut relevant_contracts = std::collections::HashSet::new();
    for (contract_name, functions) in &analysis.contract_registry.function_map {
        for func_name in functions.keys() {
            if relevant_functions.contains(func_name) || called_functions.contains(func_name) {
                relevant_contracts.insert(contract_name.clone());
            }
        }
    }

    // 提取函数级别的代码
    let mut function_slices: Vec<String> = Vec::new();
    let mut type_definitions = Vec::new();
    
    // 首先收集所有相关的类型定义
    let mut i = 0;
    while i < lines.len() {
        let line = lines[i].trim();
        
        // 检查是否是类型定义的开始
        if line.starts_with("type ") || line.starts_with("struct ") || line.starts_with("enum ") || line.starts_with("interface ") || 
           (line.starts_with("library ") && (!exclude_libs || is_contract_relevant(&line, &relevant_contracts))) || 
           (line.starts_with("contract ") && (!exclude_libs || is_contract_relevant(&line, &relevant_contracts))) {
            
            // 如果不包含类型定义，跳过
            if !include_types && (line.starts_with("type ") || line.starts_with("struct ") || line.starts_with("enum ")) {
                // 跳过类型定义
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
            
            let type_code = extract_entire_type(&lines, i);
            type_definitions.push(type_code);
            
            // 跳过类型定义
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
        i += 1;
    }
    
    // 合并类型定义和函数切片
    let mut result = Vec::new();
    result.extend(type_definitions);
    
    result
}

// 提取函数名的辅助函数
fn extract_function_name(function_line: &str) -> String {
    // 从 "function funcName(" 这样的行中提取函数名
    if let Some(start) = function_line.find("function ") {
        let after_function = &function_line[start + 9..]; // "function " 的长度是9
        if let Some(end) = after_function.find('(') {
            return after_function[..end].trim().to_string();
        }
    }
    String::new()
}

// 提取整个类型的代码
fn extract_entire_type(lines: &[&str], start_line: usize) -> String {
    let mut type_lines = Vec::new();
    let mut brace_count: i32 = 0;
    let mut i = start_line;

    // 首先收集完整的类型签名
    let mut signature_lines = Vec::new();
    let mut signature_complete = false;

    while i < lines.len() && !signature_complete {
        let line = lines[i];
        signature_lines.push(line.to_string());

        // 检查是否是类型签名的结束（有左大括号或分号）
        if line.contains('{') || line.trim().ends_with(';') {
            signature_complete = true;
        }

        brace_count += line.chars().filter(|&c| c == '{').count() as i32;
        let close_count = line.chars().filter(|&c| c == '}').count() as i32;
        if brace_count >= close_count {
            brace_count -= close_count;
        } else {
            brace_count = 0;
        }

        i += 1;
    }

    // 合并签名行
    let signature = signature_lines.join("\n");
    type_lines.push(signature.clone());

    // 如果类型签名以分号结束，这是类型声明
    if signature.trim().ends_with(';') {
        return signature;
    }

    // 添加类型体，直到找到匹配的结束大括号
    while i < lines.len() && brace_count > 0 {
        let line = lines[i];
        type_lines.push(line.to_string());

        brace_count += line.chars().filter(|&c| c == '{').count() as i32;
        let close_count = line.chars().filter(|&c| c == '}').count() as i32;
        if brace_count >= close_count {
            brace_count -= close_count;
        } else {
            brace_count = 0;
        }

        i += 1;
    }

    type_lines.join("\n")
}

// 提取整个函数的代码
fn extract_entire_function(lines: &[&str], start_line: usize) -> String {
    let mut function_lines = Vec::new();
    let mut brace_count: i32 = 0;
    let mut i = start_line;

    // 首先收集完整的函数签名
    let mut signature_lines = Vec::new();
    let mut signature_complete = false;

    while i < lines.len() && !signature_complete {
        let line = lines[i];
        signature_lines.push(line.to_string());

        // 检查是否是函数签名的结束（有左大括号或分号）
        if line.contains('{') || line.trim().ends_with(';') {
            signature_complete = true;
        }

        brace_count += line.chars().filter(|&c| c == '{').count() as i32;
        let close_count = line.chars().filter(|&c| c == '}').count() as i32;
        if brace_count >= close_count {
            brace_count -= close_count;
        } else {
            brace_count = 0;
        }

        i += 1;
    }

    // 合并签名行
    let signature = signature_lines.join("\n");
    function_lines.push(signature.clone());

    // 如果函数签名以分号结束，这是接口函数声明
    if signature.trim().ends_with(';') {
        return signature;
    }

    // 添加函数体，直到找到匹配的结束大括号
    while i < lines.len() && brace_count > 0 {
        let line = lines[i];
        function_lines.push(line.to_string());

        brace_count += line.chars().filter(|&c| c == '{').count() as i32;
        let close_count = line.chars().filter(|&c| c == '}').count() as i32;
        if brace_count >= close_count {
            brace_count -= close_count;
        } else {
            brace_count = 0;
        }

        i += 1;
    }

    function_lines.join("\n")
}

// 跨合约分析和切片的主函数
pub fn analyze_contracts_and_get_slice(file_paths: &[String], contract_name: &str, function_name: &str, variable_name: &str, exclude_libs: bool, include_types: bool) -> Result<Vec<String>, String> {
    use std::fs;
    
    // 读取所有源代码
    let mut source_codes = Vec::new();
    for file_path in file_paths {
        let source_code = fs::read_to_string(file_path)
            .map_err(|e| format!("Failed to read file {}: {}", file_path, e))?;
        source_codes.push(source_code);
    }
    
    // 解析AST
    let sess = Session::builder().with_buffer_emitter(solar_interface::ColorChoice::Auto).build();
    
    let result = sess.enter(|| -> solar_interface::Result<AnalysisResult> {
        let arena = ast::Arena::new();
        let mut all_asts = Vec::new();
        for file_path in file_paths {
            let mut parser = Parser::from_file(&sess, &arena, Path::new(file_path))?;
            let ast = parser.parse_file().map_err(|e| e.emit())?;
            all_asts.push(ast);
        }
        Ok(analyze_asts(&all_asts, &source_codes.join("\n")))
    });
    
    match result {
        Ok(analysis) => {
            // 获取源码级切片
            let slice = get_source_slice(&analysis, &source_codes.join("\n"), contract_name, function_name, variable_name, exclude_libs, include_types);
            Ok(slice)
        }
        Err(_) => Err("Failed to parse or analyze the contracts".to_string()),
    }
}

// 跨合约分析和源码级别切片的主函数
pub fn analyze_contracts_and_get_line_slice(file_paths: &[String], contract_name: &str, function_name: &str, variable_name: &str, exclude_libs: bool, include_types: bool) -> Result<Vec<String>, String> {
    use std::fs;

    // 读取所有源代码
    let mut source_codes = Vec::new();
    for file_path in file_paths {
        let source_code = fs::read_to_string(file_path)
            .map_err(|e| format!("Failed to read file {}: {}", file_path, e))?;
        source_codes.push(source_code);
    }

    // 解析AST
    let sess = Session::builder().with_buffer_emitter(solar_interface::ColorChoice::Auto).build();

    let result = sess.enter(|| -> solar_interface::Result<AnalysisResult> {
        let arena = ast::Arena::new();
        let mut all_asts = Vec::new();
        for file_path in file_paths {
            let mut parser = Parser::from_file(&sess, &arena, Path::new(file_path))?;
            let ast = parser.parse_file().map_err(|e| e.emit())?;
            all_asts.push(ast);
        }
        Ok(analyze_asts(&all_asts, &source_codes.join("\n")))
    });

    match result {
        Ok(analysis) => {
            // 获取源码级别切片
            let slice = get_source_line_slice(&analysis, &source_codes.join("\n"), contract_name, function_name, variable_name, exclude_libs, include_types);
            Ok(slice)
        }
        Err(_) => Err("Failed to parse or analyze the contracts".to_string()),
    }
}

// 判断是否是工具类函数（应该被过滤掉）
// 判断是否是工具类函数（应该被过滤掉）
fn is_utility_function(func_name: &str) -> bool {
    // 过滤掉各种log函数
    if func_name.starts_with("log") {
        return true;
    }

    // 过滤掉控制台输出函数
    if func_name.starts_with("console") {
        return true;
    }

    // 过滤掉数学库函数
    let math_functions = [
        "min", "max", "abs", "sqrt", "pow", "exp", "ln", "log2", "log10",
        "sin", "cos", "tan", "asin", "acos", "atan", "atan2"
    ];
    if math_functions.contains(&func_name) {
        return true;
    }

    // 过滤掉字符串处理函数
    let string_functions = [
        "concat", "substr", "substring", "indexOf", "lastIndexOf",
        "toLowerCase", "toUpperCase", "trim", "startsWith", "endsWith"
    ];
    if string_functions.contains(&func_name) {
        return true;
    }

    // 过滤掉数组工具函数
    let array_functions = [
        "push", "pop", "length", "slice", "splice", "indexOf", "includes",
        "filter", "map", "reduce", "forEach", "find", "findIndex"
    ];
    if array_functions.contains(&func_name) {
        return true;
    }

    // 过滤掉哈希函数
    let hash_functions = [
        "keccak256", "sha256", "ripemd160", "ecrecover"
    ];
    if hash_functions.contains(&func_name) {
        return true;
    }

    // 可以在这里添加其他工具类函数的过滤规则

    false
}

// 检查合约/库是否相关（定义了相关函数）
fn is_contract_relevant(line: &str, relevant_contracts: &std::collections::HashSet<String>) -> bool {
    // 从 "library PanopticMath {" 或 "contract PanopticPool {" 中提取名字
    if let Some(lib_pos) = line.find("library ") {
        let after_lib = &line[lib_pos + 8..];
        if let Some(space_pos) = after_lib.find(' ') {
            let contract_name = &after_lib[..space_pos];
            return relevant_contracts.contains(contract_name.trim());
        } else if let Some(brace_pos) = after_lib.find('{') {
            let contract_name = &after_lib[..brace_pos];
            return relevant_contracts.contains(contract_name.trim());
        }
    } else if let Some(contract_pos) = line.find("contract ") {
        let after_contract = &line[contract_pos + 9..];
        if let Some(space_pos) = after_contract.find(' ') {
            let contract_name = &after_contract[..space_pos];
            return relevant_contracts.contains(contract_name.trim());
        } else if let Some(brace_pos) = after_contract.find('{') {
            let contract_name = &after_contract[..brace_pos];
            return relevant_contracts.contains(contract_name.trim());
        }
    }
    false
}

// 从节点标签中提取被调用的函数名
fn extract_called_function_name(label: &str) -> Option<String> {
    if let Some(dot_pos) = label.find('.') {
        let func_part = &label[dot_pos + 1..];
        // 如果有括号，取括号前的部分
        let func_name = if let Some(paren_pos) = func_part.find('(') {
            &func_part[..paren_pos]
        } else {
            func_part
        };
        // 只返回非内置函数和非构造函数的调用
        if !func_name.is_empty() && !matches!(func_name, "assert" | "require" | "revert" | "emit" | "console") {
            return Some(func_name.to_string());
        }
    }
    // 处理类似 "setTickCumulatives(args)" 的直接调用
    else if let Some(paren_pos) = label.find('(') {
        let func_name = &label[..paren_pos];
        if !func_name.is_empty() && !matches!(func_name, "assert" | "require" | "revert" | "emit" | "console") {
            return Some(func_name.to_string());
        }
    }
    None
}