#![allow(unused)]
//!
//! 语义代码切片器
//!
//! 本模块实现了基于语义的代码切片算法，结合 LLM 语义分析
//! 和静态启发式规则，评估代码片段之间的相关性，进行智能
//! 的程序依赖图切片，用于 Solidity 安全分析。
//!

use async_trait::async_trait;
use futures::future::join_all;
use std::cmp::Ordering;
use std::collections::{BinaryHeap, HashMap, HashSet};
use std::fs::OpenOptions;
use std::io::Write;
use std::sync::{Arc, Mutex};
use tokio::sync::Semaphore;

// Function-Level CHSS 相关类型定义
#[derive(Debug, Clone)]
pub enum EdgeDecision {
    Include,
    Exclude,
    AskLLM,
}

#[derive(Debug, Clone)]
pub struct CallEdge {
    pub id: usize,
    pub caller: String,
    pub callee: String,
    pub caller_id: usize,
    pub callee_id: usize,
    pub code_line: String,
    pub return_var_used: bool,
    pub is_in_require: bool,
    pub static_score: u8,
    pub decision: EdgeDecision,
}

#[derive(Debug, Clone)]
pub struct FunctionCallInfo {
    pub callee: String,
    pub is_external: bool,
    pub receiver: Option<String>,
    pub code_snippet: String,
}

#[derive(Debug, Clone)]
pub struct VmStoreInfo {
    pub target_address: String,
    pub slot_expr: String,
    pub value_expr: String,
    pub inferred_var: Option<String>,
    pub code_snippet: String,
}

// 定义一个适配器接口，旧的图结构必须实现这个接口
#[async_trait]
pub trait SemanticGraphAdapter {
    // 获取前驱节点的 ID 列表 (用于后向切片)
    fn get_predecessors(&self, node_id: usize) -> Vec<usize>;

    // 获取节点的源码文本 (用于发给 LLM)
    // 如果旧节点只有行号，这里需要负责去源码文件中把代码读出来
    fn get_node_source(&self, node_id: usize) -> String;

    // 获取节点的类型 (可选，用于启发式过滤)
    fn is_control_node(&self, node_id: usize) -> bool;

    // 获取节点的详细信息 (用于调试)
    fn get_node_info(&self, node_id: usize) -> Option<&crate::analyzer::PdgNode>;

    // 新增：让 Adapter 负责判断这是不是关键字
    fn is_keyword(&self, token: &str) -> bool;

    // 新增：让 Adapter 负责提取变量（它可以利用底层的 AST）
    fn extract_identifiers(&self, node_id: usize) -> Vec<String>;

    // 新增：让 Adapter 提供合约上下文摘要
    fn get_contract_context_summary(&self) -> String;

    // Function-Level CHSS 扩展方法
    fn get_all_call_edges(&self) -> Vec<CallEdge>;
    fn get_function_code(&self, func_id: usize) -> String;
    fn get_function_name(&self, node_id: usize) -> Option<String>;
    fn get_contract_for_function(&self, func_id: usize) -> Option<String>;

    // AST-Level Coverage & Taint Tracking Extensions
    fn get_function_calls_in_code(&self, code: &str) -> Vec<FunctionCallInfo>;
    fn get_vm_store_accesses(&self, code: &str) -> Vec<VmStoreInfo>;
    fn infer_variable_from_slot(&self, slot_expr: &str) -> Option<String>;
}

// 1. 定义评分节点，用于优先队列排序
#[derive(Debug, Clone, PartialEq, Eq)]
struct ScoredItem {
    score: u8, // 0-100
    node_id: usize,
    depth: usize,
}

// 实现 Ord 以支持最大堆
impl Ord for ScoredItem {
    fn cmp(&self, other: &Self) -> Ordering {
        self.score.cmp(&other.score)
    }
}
impl PartialOrd for ScoredItem {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum SliceAtom {
    FullStatement(usize),
    FullVariableDeclStatement(usize),
    FullExpressionStatement(usize),
    FullReturnStatement(usize),
    FullIfStatement(usize),
    FullForStatement(usize),
    FullBlockWindow {
        block_id: usize,
        start_stmt: usize,
        end_stmt: usize,
    },
}

// 2. 定义切片器结构体
pub struct SemanticSlicer<'a, G: SemanticGraphAdapter> {
    graph: &'a G, // 持有适配器的引用
    api_key: String,
    base_url: String,
    model: String,
    score_cache: Arc<Mutex<HashMap<(usize, usize), u8>>>, // 缓存: (pred, curr) -> score
    llm_threshold: u8,                                    // 只有静态分数高于此阈值才调用LLM
    use_parallel: bool,                                   // 是否并行调用LLM
    max_concurrent: usize,                                // 最大并发数
    cache_file: Option<String>,                           // 持久化缓存文件
}

impl<'a, G: SemanticGraphAdapter> SemanticSlicer<'a, G> {
    pub fn new(graph: &'a G, api_key: String, base_url: String, model: String) -> Self {
        Self {
            graph,
            api_key,
            base_url,
            model,
            score_cache: Arc::new(Mutex::new(HashMap::new())),
            llm_threshold: 0, // 默认所有节点都调用LLM
            use_parallel: false,
            max_concurrent: 4,
            cache_file: None,
        }
    }

    pub fn new_with_threshold(
        graph: &'a G,
        api_key: String,
        base_url: String,
        model: String,
        llm_threshold: u8,
    ) -> Self {
        Self {
            graph,
            api_key,
            base_url,
            model,
            score_cache: Arc::new(Mutex::new(HashMap::new())),
            llm_threshold,
            use_parallel: false,
            max_concurrent: 4,
            cache_file: None,
        }
    }

    pub fn new_with_options(
        graph: &'a G,
        api_key: String,
        base_url: String,
        model: String,
        llm_threshold: u8,
        use_parallel: bool,
        max_concurrent: usize,
        cache_file: Option<String>,
    ) -> Self {
        let mut slicer = Self {
            graph,
            api_key,
            base_url,
            model,
            score_cache: Arc::new(Mutex::new(HashMap::new())),
            llm_threshold,
            use_parallel,
            max_concurrent,
            cache_file: cache_file.clone(),
        };

        // 加载持久化缓存
        if let Some(ref file) = cache_file {
            slicer.load_cache(file);
        }

        slicer
    }

    // 加载缓存
    fn load_cache(&mut self, file_path: &str) {
        if let Ok(content) = std::fs::read_to_string(file_path) {
            if let Ok(cache) = serde_json::from_str::<HashMap<String, u8>>(&content) {
                for (key, val) in cache {
                    if let Some((pred, curr)) = Self::parse_cache_key(&key) {
                        if let Ok(mut cache) = self.score_cache.lock() {
                            cache.insert((pred, curr), val);
                        }
                    }
                }
                println!(
                    "📦 Loaded {} cached scores from {}",
                    self.score_cache
                        .lock()
                        .map(|cache| cache.len())
                        .unwrap_or(0),
                    file_path
                );
            }
        }
    }

    // 保存缓存
    fn save_cache(&self, file_path: &str) {
        let mut cache = HashMap::new();
        if let Ok(score_cache) = self.score_cache.lock() {
            for ((pred, curr), score) in score_cache.iter() {
                cache.insert(format!("{}:{}", pred, curr), *score);
            }
        }
        if let Ok(json) = serde_json::to_string_pretty(&cache) {
            let _ = std::fs::write(file_path, json);
        }
    }

    // 解析缓存键
    fn parse_cache_key(key: &str) -> Option<(usize, usize)> {
        let parts: Vec<&str> = key.split(':').collect();
        if parts.len() == 2 {
            if let (Ok(pred), Ok(curr)) = (parts[0].parse(), parts[1].parse()) {
                return Some((pred, curr));
            }
        }
        None
    }

    // 核心：基于 LLM 的切片主循环
    pub async fn run_slicing(&mut self, sink_nodes: Vec<usize>) -> HashSet<SliceAtom> {
        self.run_slicing_with_max_depth(sink_nodes, usize::MAX)
            .await
    }

    pub async fn run_slicing_with_max_depth(
        &mut self,
        sink_nodes: Vec<usize>,
        max_depth: usize,
    ) -> HashSet<SliceAtom> {
        let mut log_file = OpenOptions::new()
            .create(true)
            .append(true)
            .open("analysis.log")
            .unwrap();

        writeln!(log_file, "🚀 STARTING SEMANTIC SLICING").unwrap();
        writeln!(log_file, "📍 Sink Nodes: {:?}", sink_nodes).unwrap();
        writeln!(log_file, "📏 Max dependency depth: {}", max_depth).unwrap();

        // 记录每个sink node的详细信息
        for &node_id in &sink_nodes {
            if let Some(node) = self.graph.get_node_info(node_id) {
                writeln!(
                    log_file,
                    "📋 Sink Node {} Details: kind={:?}, label='{}', function_context={:?}",
                    node_id, node.kind, node.label, node.function_context
                )
                .unwrap();
            } else {
                writeln!(log_file, "❌ Sink Node {} not found in graph", node_id).unwrap();
            }
        }

        let mut pq = BinaryHeap::new();
        let mut result_slice = HashSet::new();
        let mut visited = HashSet::new();

        // 初始化：Sink 点满分入队
        for sink in sink_nodes {
            pq.push(ScoredItem {
                score: 100,
                node_id: sink,
                depth: 0,
            });
            writeln!(log_file, "➕ Added sink node {} with score 100", sink).unwrap();
        }

        let mut iteration = 0;
        while let Some(item) = pq.pop() {
            iteration += 1;
            writeln!(
                log_file,
                "\n🔄 Iteration {}: Processing node {} with score {}",
                iteration, item.node_id, item.score
            )
            .unwrap();

            // DEBUG: Print node details
            if let Some(node) = self.graph.get_node_info(item.node_id) {
                writeln!(
                    log_file,
                    "🔍 Node Details: PdgId={}, Kind={:?}, Label='{}'",
                    node.id, node.kind, node.label
                )
                .unwrap();
            }

            if item.score < 20 {
                writeln!(
                    log_file,
                    "✂️  Pruning node {} (score {} < 20)",
                    item.node_id, item.score
                )
                .unwrap();
                continue;
            }
            if !visited.insert(item.node_id) {
                writeln!(
                    log_file,
                    "⏭️  Skipping already visited node {}",
                    item.node_id
                )
                .unwrap();
                continue;
            }
            result_slice.insert(item.node_id);
            writeln!(
                log_file,
                "✅ Added node {} to slice (total: {})",
                item.node_id,
                result_slice.len()
            )
            .unwrap();

            if item.depth >= max_depth {
                writeln!(
                    log_file,
                    "📏 Reached max depth {} at node {}, not expanding predecessors",
                    max_depth, item.node_id
                )
                .unwrap();
                continue;
            }

            let _current_code = self.graph.get_node_source(item.node_id);
            let preds = self.graph.get_predecessors(item.node_id);

            writeln!(
                log_file,
                "🔍 Analyzing predecessors of node {}: {:?}",
                item.node_id, preds
            )
            .unwrap();

            // 准备批量评分
            let pred_list: Vec<usize> = preds
                .iter()
                .filter(|&&pred_id| !visited.contains(&pred_id))
                .copied()
                .collect();

            if pred_list.is_empty() {
                writeln!(log_file, "ℹ️  No unvisited predecessors").unwrap();
                writeln!(log_file, "📋 Current queue size: {}", pq.len()).unwrap();
                continue;
            }

            // 并发或串行处理依赖评分
            let scores = if self.use_parallel && pred_list.len() > 1 {
                writeln!(
                    log_file,
                    "⚡ Parallel processing {} predecessors (max {} concurrent)",
                    pred_list.len(),
                    self.max_concurrent
                )
                .unwrap();
                self.calculate_relevance_batch_parallel(&pred_list, item.node_id, iteration)
                    .await
            } else {
                // 串行处理
                let mut scores = Vec::new();
                for &pred_id in &pred_list {
                    scores.push(
                        self.calculate_relevance(pred_id, item.node_id, iteration)
                            .await,
                    );
                }
                scores
            };

            // 处理结果
            for (i, &pred_id) in pred_list.iter().enumerate() {
                let rel_score = scores[i];

                // DEBUG: Print predecessor details
                if let Some(node) = self.graph.get_node_info(pred_id) {
                    writeln!(
                        log_file,
                        "🔍 Pred Node {} Details: PdgId={}, Kind={:?}, Label='{}'",
                        pred_id, node.id, node.kind, node.label
                    )
                    .unwrap();
                }

                writeln!(
                    log_file,
                    "📊 Relevance score for pred {} -> curr {}: {}",
                    pred_id, item.node_id, rel_score
                )
                .unwrap();

                // 距离衰减
                let decayed = (rel_score as f32 * 0.95) as u8;
                writeln!(log_file, "📉 Decayed score: {} -> {}", rel_score, decayed).unwrap();

                if decayed >= 20 {
                    pq.push(ScoredItem {
                        score: decayed,
                        node_id: pred_id,
                        depth: item.depth + 1,
                    });
                    writeln!(
                        log_file,
                        "➕ Enqueued predecessor {} with score {}",
                        pred_id, decayed
                    )
                    .unwrap();
                } else {
                    writeln!(
                        log_file,
                        "✂️  Not enqueuing predecessor {} (decayed score {} < 20)",
                        pred_id, decayed
                    )
                    .unwrap();
                }
            }

            writeln!(log_file, "📋 Current queue size: {}", pq.len()).unwrap();
        }

        writeln!(log_file, "\n🎉 SLICING COMPLETED").unwrap();
        writeln!(
            log_file,
            "📊 Final slice contains {} nodes: {:?}",
            result_slice.len(),
            result_slice
        )
        .unwrap();
        writeln!(log_file, "🏁 END SEMANTIC SLICING\n").unwrap();

        // 保存缓存
        if let Some(ref file) = self.cache_file {
            self.save_cache(file);
            writeln!(log_file, "💾 Saved cache to {}", file).unwrap();
        }

        let mut atoms = HashSet::new();
        for &id in &result_slice {
            atoms.insert(SliceAtom::FullStatement(id));
        }

        atoms
    }

    // 并行批量评分
    async fn calculate_relevance_batch_parallel(
        &self,
        pred_ids: &[usize],
        curr_id: usize,
        depth: usize,
    ) -> Vec<u8> {
        // 使用信号量控制并发
        let semaphore = Arc::new(Semaphore::new(self.max_concurrent));
        let mut tasks = Vec::new();

        for &pred_id in pred_ids {
            let sem = Arc::clone(&semaphore);
            let task = async move {
                let _permit = sem.acquire().await.unwrap();
                self.calculate_relevance(pred_id, curr_id, depth).await
            };
            tasks.push(task);
        }

        join_all(tasks).await
    }

    // 评分逻辑：只使用静态启发式。LLM 参与会引入不确定性并污染切片边界。
    async fn calculate_relevance(&self, pred_id: usize, curr_id: usize, depth: usize) -> u8 {
        let mut log_file = OpenOptions::new()
            .create(true)
            .append(true)
            .open("analysis.log")
            .unwrap();

        writeln!(
            log_file,
            "🔍 Calculating relevance for pred_id {} -> curr_id {} at depth {}",
            pred_id, curr_id, depth
        )
        .unwrap();

        if let Ok(cache) = self.score_cache.lock() {
            if let Some(score) = cache.get(&(pred_id, curr_id)) {
                writeln!(
                    log_file,
                    "💾 Cache hit for pred_id {} -> curr_id {}: {}",
                    pred_id, curr_id, score
                )
                .unwrap();
                return *score;
            }
        }

        // 首先尝试静态启发式评分
        let static_score = self.static_relevance_score(pred_id, curr_id, depth);
        writeln!(log_file, "📊 Static heuristic score: {}", static_score).unwrap();
        writeln!(
            log_file,
            "🔒 LLM relevance scoring disabled; using static score"
        )
        .unwrap();
        self.store_score(pred_id, curr_id, static_score);
        static_score
    }

    fn store_score(&self, pred_id: usize, curr_id: usize, score: u8) {
        if let Ok(mut cache) = self.score_cache.lock() {
            cache.insert((pred_id, curr_id), score);
        }
    }

    // 静态启发式评分：基于变量重叠和函数调用深度
    fn static_relevance_score(&self, pred_id: usize, curr_id: usize, depth: usize) -> u8 {
        let mut score = 0u8;

        // 1. 变量重叠度
        let pred_vars: HashSet<_> = self
            .graph
            .extract_identifiers(pred_id)
            .into_iter()
            .collect();
        let curr_vars: HashSet<_> = self
            .graph
            .extract_identifiers(curr_id)
            .into_iter()
            .collect();
        let overlap: HashSet<_> = pred_vars.intersection(&curr_vars).collect();

        // Improved overlap calculation: use the maximum ratio of overlap to either set
        let overlap_ratio = if !pred_vars.is_empty() && !curr_vars.is_empty() {
            let p_ratio = overlap.len() as f32 / pred_vars.len() as f32;
            let c_ratio = overlap.len() as f32 / curr_vars.len() as f32;
            p_ratio.max(c_ratio)
        } else if !pred_vars.is_empty() {
            overlap.len() as f32 / pred_vars.len() as f32
        } else if !curr_vars.is_empty() {
            overlap.len() as f32 / curr_vars.len() as f32
        } else {
            0.0
        };
        score += (overlap_ratio * 40.0) as u8; // 最多40分

        // 2. 函数调用相似性（简化：重用变量重叠逻辑）
        // 这里可以扩展为专门的函数调用提取，但暂时用标识符重叠近似
        score += (overlap_ratio * 30.0) as u8; // 最多30分

        // 3. 深度衰减：深度越高，基础分数降低
        let depth_penalty = (depth as f32 * 2.0).min(20.0) as u8; // 最多20分惩罚
        score = score.saturating_sub(depth_penalty);

        // 4. 数据流复杂度奖励：如果有复杂的表达式，给予奖励
        if self.has_complex_data_flow(&self.graph.get_node_source(pred_id)) {
            score += 10;
        }

        // Guarantee minimum score if there is variable overlap (strong indicator of data dependency)
        // This prevents premature pruning of relevant nodes that have many other variables
        if !overlap.is_empty() {
            score = score.max(25);
        }

        score.min(100)
    }

    // 检查是否有复杂数据流（算术运算、多重赋值等）
    fn has_complex_data_flow(&self, code: &str) -> bool {
        code.contains(" + ")
            || code.contains(" - ")
            || code.contains(" * ")
            || code.contains(" / ")
            || code.contains(" += ")
            || code.contains(" -= ")
            || code.contains(" *= ")
            || code.contains(" /= ")
            || code.matches(" = ").count() > 1
    }

    // 判断代码块是否与目标相关
    pub async fn is_code_relevant(
        &self,
        code: &str,
        target_variable: &str,
        _full_context: &str,
        _related_functions: &[String],
    ) -> bool {
        let mut log_file = OpenOptions::new()
            .create(true)
            .append(true)
            .open("analysis.log")
            .unwrap();

        writeln!(log_file, "=== STARTING RELEVANCE ANALYSIS ===").unwrap();
        writeln!(log_file, "Target Variable: {}", target_variable).unwrap();
        writeln!(
            log_file,
            "Code to Analyze: {}",
            code.lines().next().unwrap_or("").trim()
        )
        .unwrap();

        // 静态规则：如果代码直接包含目标变量，认为是相关的
        if code.contains(target_variable) {
            writeln!(
                log_file,
                "✅ DIRECT MATCH: Code contains target variable '{}'",
                target_variable
            )
            .unwrap();
            return true;
        }

        // 静态分析：跨合约依赖和返回值使用
        // 简化：暂时移除复杂的字符串解析，交由 Adapter 处理
        // if self.analyze_cross_contract_relevance(code, target_variable, full_context) {
        //     writeln!(log_file, "✅ STATIC ANALYSIS: Cross-contract relevance detected for '{}'", target_variable).unwrap();
        //     return true;
        // }

        writeln!(
            log_file,
            "🔒 No direct static match; LLM relevance fallback disabled, marking not relevant"
        )
        .unwrap();
        writeln!(log_file, "=== END RELEVANCE ANALYSIS ===\n").unwrap();
        false
    }

    // 代码补全方法（公开接口）
    pub async fn complete_code(
        &self,
        slice_code: &str,
        source_code: &str,
        target_function: &str,
    ) -> Result<String, Box<dyn std::error::Error>> {
        complete_missing_code(self, slice_code, source_code, target_function).await
    }

    // S1.2 PoC 质量分析 - 增强版
    pub async fn analyze_poc_quality(
        &self,
        slice_code: &str,
    ) -> Result<String, Box<dyn std::error::Error>> {
        let mut log_file = OpenOptions::new()
            .create(true)
            .append(true)
            .open("analysis.log")?;

        writeln!(log_file, "\n{}", "=".repeat(80))?;
        writeln!(log_file, "=== STARTING POC QUALITY ANALYSIS (S1.2) ===")?;
        writeln!(log_file, "{}\n", "=".repeat(80))?;

        // 🔍 步骤 1: 静态作弊码分析（环境真实性）
        println!("\n🔍 Step 1: Analyzing Cheatcode Usage (Environment Authenticity)...");
        let cheatcode_analysis = self.analyze_cheatcodes(slice_code);
        writeln!(log_file, "=== STEP 1: CHEATCODE ANALYSIS (STATIC) ===")?;
        writeln!(log_file, "{:#?}", cheatcode_analysis)?;

        // 🔍 步骤 2: 断言逻辑分析
        println!("🔍 Step 2: Analyzing Assertion Logic...");
        let assertion_analysis = self.analyze_assertions(slice_code);
        writeln!(log_file, "\n=== STEP 2: ASSERTION ANALYSIS (STATIC) ===")?;
        writeln!(log_file, "{:#?}", assertion_analysis)?;

        writeln!(
            log_file,
            "🔒 Remote PoC quality analysis disabled; returning static report"
        )?;
        let report =
            self.generate_static_report(&cheatcode_analysis, &assertion_analysis, slice_code);
        writeln!(log_file, "=== STATIC POC QUALITY ANALYSIS RESULT ===")?;
        writeln!(log_file, "{}", report)?;
        writeln!(log_file, "=== END POC QUALITY ANALYSIS ===")?;
        Ok(report)
    }

    // Disabled legacy remote relevance helper.
    async fn call_llm_for_relevance(
        &self,
        pred_code: &str,
        curr_code: &str,
        depth: usize,
    ) -> Result<u8, Box<dyn std::error::Error>> {
        let _ = (self, pred_code, curr_code, depth);
        Err("Remote relevance scoring is disabled".into())
    }

    // Disabled legacy remote relevance helper.
    async fn call_llm_with_context_and_related(
        &self,
        code: &str,
        target_variable: &str,
        _full_context: &str,
        related_functions: &[String],
    ) -> Result<String, Box<dyn std::error::Error>> {
        let _ = (self, code, target_variable, related_functions);
        Err("Remote relevance fallback is disabled".into())
    }

    // 静态分析作弊码使用情况
    fn analyze_cheatcodes(&self, code: &str) -> Vec<CheatcodeUsage> {
        let mut cheatcodes = Vec::new();
        let dangerous_cheats = [
            "vm.store",          // 直接修改存储
            "vm.load",           // 直接读取存储
            "vm.mockCall",       // 模拟调用
            "vm.mockCallRevert", // 模拟回滚
            "vm.etch",           // 修改代码
            "vm.deal",           // 修改余额
            "vm.prank",          // 临时切换调用者
            "vm.startPrank",     // 持续切换调用者
            "vm.warp",           // 时间跳跃
            "vm.roll",           // 区块跳跃
            "vm.setNonce",       // 设置 nonce
            "vm.chainId",        // 修改链ID
            "vm.coinbase",       // 修改矿工地址
            "vm.difficulty",     // 修改难度
            "vm.fee",            // 修改基础费用
            "vm.prevrandao",     // 修改随机数
        ];

        for (line_num, line) in code.lines().enumerate() {
            for cheat in &dangerous_cheats {
                if line.contains(cheat) {
                    let risk_level = match *cheat {
                        "vm.store" | "vm.etch" => RiskLevel::Critical,
                        "vm.mockCall" | "vm.mockCallRevert" => RiskLevel::High,
                        "vm.deal" | "vm.prank" | "vm.startPrank" => RiskLevel::Medium,
                        _ => RiskLevel::Low,
                    };

                    cheatcodes.push(CheatcodeUsage {
                        cheatcode: cheat.to_string(),
                        line_number: line_num + 1,
                        line_content: line.trim().to_string(),
                        risk_level,
                        potential_issue: get_cheatcode_issue(cheat),
                    });
                }
            }
        }

        cheatcodes
    }

    // 分析断言语句
    fn analyze_assertions(&self, code: &str) -> Vec<AssertionInfo> {
        let mut assertions = Vec::new();

        let assertion_types = [
            "assertEq",
            "assertNotEq",
            "assertGt",
            "assertGe",
            "assertLt",
            "assertLe",
            "assertTrue",
            "assertFalse",
            "assert",
            "require",
            "vm.expectRevert",
        ];

        for (line_num, line) in code.lines().enumerate() {
            let trimmed = line.trim();

            // 跳过注释
            if trimmed.starts_with("//") || trimmed.starts_with("/*") || trimmed.starts_with("*") {
                continue;
            }

            for assert_type in &assertion_types {
                if trimmed.contains(assert_type) {
                    let assertion_quality = evaluate_assertion_quality(trimmed, assert_type);

                    assertions.push(AssertionInfo {
                        assertion_type: assert_type.to_string(),
                        line_number: line_num + 1,
                        line_content: trimmed.to_string(),
                        quality: assertion_quality,
                        issues: get_assertion_issues(trimmed, assert_type),
                    });
                }
            }
        }

        assertions
    }

    // 生成静态分析报告
    fn generate_static_report(
        &self,
        cheatcode_analysis: &[CheatcodeUsage],
        assertion_analysis: &[AssertionInfo],
        slice_code: &str,
    ) -> String {
        use std::collections::HashMap;
        let mut report = String::new();

        report.push_str("\n");
        report.push_str("╔════════════════════════════════════════════════════════════════════╗\n");
        report.push_str("║           S1.2 PoC Quality Analysis Report (Static)                ║\n");
        report.push_str("╚════════════════════════════════════════════════════════════════════╝\n");
        report.push_str("\n");

        // ========== 1. 环境真实性分析 ==========
        report
            .push_str("┌─────────────────────────────────────────────────────────────────────┐\n");
        report
            .push_str("│ 📋 1. Environment Authenticity Analysis                             │\n");
        report
            .push_str("└─────────────────────────────────────────────────────────────────────┘\n");
        report.push_str("\n");

        if cheatcode_analysis.is_empty() {
            report.push_str("✅ No cheatcodes detected - Environment appears authentic\n\n");
        } else {
            report.push_str(&format!(
                "⚠️  Detected {} cheatcode usage(s):\n\n",
                cheatcode_analysis.len()
            ));

            // 按风险级别分组
            let mut by_risk: HashMap<String, Vec<&CheatcodeUsage>> = HashMap::new();
            for cheat in cheatcode_analysis {
                let risk = format!("{:?}", cheat.risk_level);
                by_risk.entry(risk).or_insert_with(Vec::new).push(cheat);
            }

            let lines: Vec<&str> = slice_code.lines().collect();

            for risk_level in &["Critical", "High", "Medium", "Low"] {
                if let Some(cheats) = by_risk.get(*risk_level) {
                    let icon = match *risk_level {
                        "Critical" => "🔴",
                        "High" => "🟠",
                        "Medium" => "🟡",
                        _ => "🔵",
                    };

                    report.push_str(&format!("\n{} {} Risk Level:\n", icon, risk_level));
                    report.push_str(&format!("   {} cheatcode(s) detected\n\n", cheats.len()));

                    for (idx, cheat) in cheats.iter().enumerate() {
                        report.push_str(&format!(
                            "   [{}.{}] {} (Line {})\n",
                            risk_level,
                            idx + 1,
                            cheat.cheatcode,
                            cheat.line_number
                        ));
                        report.push_str(&format!("   ├─ Issue: {}\n", cheat.potential_issue));
                        report.push_str("   └─ Code Context:\n");

                        // 提取代码上下文（前后2行）
                        let line_idx = cheat.line_number.saturating_sub(1);
                        let start = line_idx.saturating_sub(2);
                        let end = (line_idx + 3).min(lines.len());

                        for i in start..end {
                            if i < lines.len() {
                                let marker = if i == line_idx { ">>>" } else { "   " };
                                report.push_str(&format!(
                                    "      {} {:3} | {}\n",
                                    marker,
                                    i + 1,
                                    lines[i]
                                ));
                            }
                        }
                        report.push_str("\n");
                    }
                }
            }

            // 关键检查项
            report.push_str("🔍 Key Checks:\n");
            let has_store = cheatcode_analysis.iter().any(|c| c.cheatcode == "vm.store");
            let has_etch = cheatcode_analysis.iter().any(|c| c.cheatcode == "vm.etch");
            let has_mock = cheatcode_analysis
                .iter()
                .any(|c| c.cheatcode.contains("mockCall"));

            if has_store {
                report.push_str(
                    "   ❌ CRITICAL: vm.store detected - May violate immutable constraints\n",
                );
            }
            if has_etch {
                report.push_str("   ❌ CRITICAL: vm.etch detected - Impossible on mainnet\n");
            }
            if has_mock {
                report.push_str(
                    "   ⚠️  WARNING: mockCall detected - Verify external call behavior\n",
                );
            }
            if !has_store && !has_etch && !has_mock {
                report.push_str("   ✓ No critical environment violations detected\n");
            }
            report.push_str("\n");
        }

        // ========== 2. 断言逻辑有效性分析 ==========
        report
            .push_str("┌─────────────────────────────────────────────────────────────────────┐\n");
        report
            .push_str("│ 📋 2. Assertion Logic Validity Analysis                             │\n");
        report
            .push_str("└─────────────────────────────────────────────────────────────────────┘\n");
        report.push_str("\n");

        if assertion_analysis.is_empty() {
            report.push_str("❌ WARNING: No assertions found in the slice!\n");
            report.push_str("   This PoC may lack proper validation logic.\n\n");
        } else {
            report.push_str(&format!(
                "✅ Found {} assertion(s):\n\n",
                assertion_analysis.len()
            ));

            // 按质量分组
            let mut by_quality: HashMap<String, Vec<&AssertionInfo>> = HashMap::new();
            for assertion in assertion_analysis {
                let quality = format!("{:?}", assertion.quality);
                by_quality
                    .entry(quality)
                    .or_insert_with(Vec::new)
                    .push(assertion);
            }

            let lines: Vec<&str> = slice_code.lines().collect();

            for quality_level in &["Valid", "Suspicious", "Invalid"] {
                if let Some(assertions) = by_quality.get(*quality_level) {
                    let icon = match *quality_level {
                        "Valid" => "✅",
                        "Suspicious" => "⚠️ ",
                        _ => "❌",
                    };

                    report.push_str(&format!("\n{} {} Assertions:\n", icon, quality_level));
                    report.push_str(&format!(
                        "   {} assertion(s) detected\n\n",
                        assertions.len()
                    ));

                    for (idx, assertion) in assertions.iter().enumerate() {
                        report.push_str(&format!(
                            "   [{}.{}] {} (Line {})\n",
                            quality_level,
                            idx + 1,
                            assertion.assertion_type,
                            assertion.line_number
                        ));

                        if !assertion.issues.is_empty() {
                            report.push_str(&format!("   ├─ Issues: {}\n", assertion.issues));
                        }

                        report.push_str("   └─ Code Context:\n");

                        // 提取代码上下文（前后2行）
                        let line_idx = assertion.line_number.saturating_sub(1);
                        let start = line_idx.saturating_sub(2);
                        let end = (line_idx + 3).min(lines.len());

                        for i in start..end {
                            if i < lines.len() {
                                let marker = if i == line_idx { ">>>" } else { "   " };
                                report.push_str(&format!(
                                    "      {} {:3} | {}\n",
                                    marker,
                                    i + 1,
                                    lines[i]
                                ));
                            }
                        }
                        report.push_str("\n");
                    }
                }
            }

            // 统计信息
            let valid_count = by_quality.get("Valid").map_or(0, |v| v.len());
            let suspicious_count = by_quality.get("Suspicious").map_or(0, |v| v.len());
            let invalid_count = by_quality.get("Invalid").map_or(0, |v| v.len());

            report.push_str("📊 Summary:\n");
            report.push_str(&format!(
                "   Valid assertions:      {} / {}\n",
                valid_count,
                assertion_analysis.len()
            ));
            report.push_str(&format!(
                "   Suspicious assertions: {} / {}\n",
                suspicious_count,
                assertion_analysis.len()
            ));
            report.push_str(&format!(
                "   Invalid assertions:    {} / {}\n",
                invalid_count,
                assertion_analysis.len()
            ));

            if invalid_count > 0 || suspicious_count as f64 / assertion_analysis.len() as f64 > 0.5
            {
                report.push_str("\n   ⚠️  WARNING: PoC may have weak assertion logic!\n");
            } else if valid_count == assertion_analysis.len() {
                report.push_str("\n   ✅ All assertions appear valid\n");
            }
            report.push_str("\n");
        }

        // ========== 3. 总体评估 ==========
        report
            .push_str("┌─────────────────────────────────────────────────────────────────────┐\n");
        report
            .push_str("│ 📋 3. Overall Assessment                                            │\n");
        report
            .push_str("└─────────────────────────────────────────────────────────────────────┘\n");
        report.push_str("\n");

        let has_critical_cheats = cheatcode_analysis
            .iter()
            .any(|c| matches!(c.risk_level, RiskLevel::Critical));
        let has_no_assertions = assertion_analysis.is_empty();
        let has_invalid_assertions = assertion_analysis
            .iter()
            .any(|a| matches!(a.quality, AssertionQuality::Invalid));

        if has_critical_cheats {
            report.push_str("❌ REJECT: Critical cheatcode violations detected\n");
            report.push_str("   The PoC modifies state in ways impossible on mainnet.\n");
        } else if has_no_assertions {
            report.push_str("❌ REJECT: No validation assertions found\n");
            report.push_str("   The PoC lacks proper vulnerability verification.\n");
        } else if has_invalid_assertions {
            report.push_str("⚠️  SUSPICIOUS: Invalid or trivial assertions detected\n");
            report.push_str("   Manual review recommended.\n");
        } else {
            report.push_str("✅ PASS: PoC appears to have reasonable quality\n");
            report.push_str("   Environment setup is realistic and assertions are valid.\n");
        }

        report.push_str("\n");
        report.push_str("╔════════════════════════════════════════════════════════════════════╗\n");
        report.push_str("║                      End of Analysis                               ║\n");
        report.push_str("╚════════════════════════════════════════════════════════════════════╝\n");

        report
    }
}

// 断言信息结构
#[derive(Debug, Clone)]
pub struct AssertionInfo {
    pub assertion_type: String,
    pub line_number: usize,
    pub line_content: String,
    pub quality: AssertionQuality,
    pub issues: String,
}

#[derive(Debug, Clone, PartialEq)]
pub enum AssertionQuality {
    Valid,      // 有效的断言
    Suspicious, // 可疑的断言
    Invalid,    // 无效的断言
}

// 评估断言质量
fn evaluate_assertion_quality(line: &str, assert_type: &str) -> AssertionQuality {
    // 检测恒真断言
    if line.contains("assert(true)") || line.contains("assertTrue(true)") {
        return AssertionQuality::Invalid;
    }

    // 检测恒假断言
    if line.contains("assert(false)") || line.contains("assertFalse(false)") {
        return AssertionQuality::Invalid;
    }

    // 检测自比较 assertEq(x, x)
    if assert_type.contains("assertEq") {
        if let Some(start) = line.find('(') {
            if let Some(end) = line.rfind(')') {
                let args = &line[start + 1..end];
                let parts: Vec<&str> = args.split(',').map(|s| s.trim()).collect();
                if parts.len() == 2 && parts[0] == parts[1] {
                    return AssertionQuality::Invalid;
                }
            }
        }
    }

    // 检测空消息的断言（可疑）
    if line.matches('"').count() == 0 && line.contains("assert") {
        return AssertionQuality::Suspicious;
    }

    AssertionQuality::Valid
}

// 获取断言问题描述
fn get_assertion_issues(line: &str, assert_type: &str) -> String {
    let mut issues = Vec::new();

    if line.contains("assert(true)") {
        issues.push("Tautology - always passes");
    }

    if assert_type.contains("assertEq") {
        if let Some(start) = line.find('(') {
            if let Some(end) = line.rfind(')') {
                let args = &line[start + 1..end];
                let parts: Vec<&str> = args.split(',').map(|s| s.trim()).collect();
                if parts.len() == 2 && parts[0] == parts[1] {
                    issues.push("Self-comparison");
                }
            }
        }
    }

    if line.matches('"').count() == 0 {
        issues.push("No error message");
    }

    issues.join(", ")
}

// 作弊码使用信息结构
#[derive(Debug, Clone)]
pub struct CheatcodeUsage {
    pub cheatcode: String,
    pub line_number: usize,
    pub line_content: String,
    pub risk_level: RiskLevel,
    pub potential_issue: String,
}

#[derive(Debug, Clone, PartialEq)]
pub enum RiskLevel {
    Critical, // 直接修改不可变状态
    High,     // 模拟关键调用
    Medium,   // 可能不真实的环境设置
    Low,      // 常规测试辅助
}

fn get_cheatcode_issue(cheatcode: &str) -> String {
    match cheatcode {
        "vm.store" => {
            "Directly modifies storage - may violate private/immutable constraints".to_string()
        }
        "vm.etch" => "Modifies deployed bytecode - impossible on mainnet".to_string(),
        "vm.mockCall" => "Mocks external calls - may hide real contract behavior".to_string(),
        "vm.mockCallRevert" => "Mocks reverts - may bypass real security checks".to_string(),
        "vm.deal" => "Artificially sets ETH balance - may not reflect real conditions".to_string(),
        "vm.prank" | "vm.startPrank" => "Impersonates addresses - verify if realistic".to_string(),
        "vm.warp" => "Time manipulation - verify if realistic for vulnerability".to_string(),
        "vm.roll" => "Block manipulation - verify if realistic for vulnerability".to_string(),
        _ => "General environment manipulation - verify necessity".to_string(),
    }
}

// ==================== 代码补全功能 ====================

/// 检测切片代码中缺失的类型和接口
pub fn detect_missing_types(slice_code: &str) -> Vec<String> {
    let cleaned = strip_comments_and_strings(slice_code);
    let tokens = tokenize_solidity(&cleaned);
    let defined_types = collect_defined_type_names(&tokens);
    let mut missing_types = HashSet::new();

    for window in tokens.windows(2) {
        if window[0] == "new" && looks_like_custom_type(&window[1]) {
            missing_types.insert(window[1].clone());
        }
    }

    for window in tokens.windows(3) {
        if window[1] == "." && looks_like_custom_type(&window[0]) {
            missing_types.insert(window[0].clone());
        }

        if looks_like_custom_type(&window[0])
            && is_identifier(&window[1])
            && !is_solidity_keyword(&window[0])
        {
            missing_types.insert(window[0].clone());
        }
    }

    let mut missing_types: Vec<String> = missing_types
        .into_iter()
        .filter(|name| !defined_types.contains(name) && !is_solidity_keyword(name))
        .collect();

    missing_types.sort();
    missing_types.dedup();
    missing_types
}

fn collect_defined_type_names(tokens: &[String]) -> HashSet<String> {
    let mut defined = HashSet::new();
    for window in tokens.windows(2) {
        if matches!(
            window[0].as_str(),
            "contract" | "interface" | "library" | "struct" | "enum" | "error" | "type"
        ) {
            defined.insert(window[1].clone());
        }
    }
    defined
}

fn tokenize_solidity(code: &str) -> Vec<String> {
    let mut tokens = Vec::new();
    let mut current = String::new();
    for ch in code.chars() {
        if ch.is_ascii_alphanumeric() || ch == '_' {
            current.push(ch);
        } else {
            if !current.is_empty() {
                tokens.push(std::mem::take(&mut current));
            }
            if ch == '.' || ch == '[' || ch == ']' {
                tokens.push(ch.to_string());
            }
        }
    }
    if !current.is_empty() {
        tokens.push(current);
    }
    tokens
}

fn strip_comments_and_strings(code: &str) -> String {
    let mut out = String::with_capacity(code.len());
    let mut chars = code.chars().peekable();
    let mut in_line_comment = false;
    let mut in_block_comment = false;
    let mut in_string: Option<char> = None;
    let mut escaped = false;

    while let Some(ch) = chars.next() {
        if in_line_comment {
            if ch == '\n' {
                in_line_comment = false;
                out.push('\n');
            } else {
                out.push(' ');
            }
            continue;
        }

        if in_block_comment {
            if ch == '*' && chars.peek() == Some(&'/') {
                chars.next();
                in_block_comment = false;
                out.push(' ');
                out.push(' ');
            } else if ch == '\n' {
                out.push('\n');
            } else {
                out.push(' ');
            }
            continue;
        }

        if let Some(quote) = in_string {
            if ch == '\n' {
                in_string = None;
                out.push('\n');
            } else {
                out.push(' ');
                if ch == quote && !escaped {
                    in_string = None;
                }
                escaped = ch == '\\' && !escaped;
                if ch != '\\' {
                    escaped = false;
                }
            }
            continue;
        }

        if ch == '/' && chars.peek() == Some(&'/') {
            chars.next();
            in_line_comment = true;
            out.push(' ');
            out.push(' ');
        } else if ch == '/' && chars.peek() == Some(&'*') {
            chars.next();
            in_block_comment = true;
            out.push(' ');
            out.push(' ');
        } else if ch == '"' || ch == '\'' {
            in_string = Some(ch);
            escaped = false;
            out.push(' ');
        } else {
            out.push(ch);
        }
    }

    out
}

fn looks_like_custom_type(name: &str) -> bool {
    name.chars()
        .next()
        .map_or(false, |ch| ch.is_ascii_uppercase())
        && !looks_like_constant(name)
}

fn looks_like_constant(name: &str) -> bool {
    name.contains('_')
        && name
            .chars()
            .all(|ch| ch.is_ascii_uppercase() || ch.is_ascii_digit() || ch == '_')
}

fn is_identifier(value: &str) -> bool {
    let mut chars = value.chars();
    let Some(first) = chars.next() else {
        return false;
    };
    (first.is_ascii_alphabetic() || first == '_')
        && chars.all(|ch| ch.is_ascii_alphanumeric() || ch == '_')
}

fn is_solidity_keyword(token: &str) -> bool {
    matches!(
        token,
        "address"
            | "bool"
            | "bytes"
            | "bytes32"
            | "int"
            | "int24"
            | "int56"
            | "int128"
            | "int256"
            | "string"
            | "uint"
            | "uint8"
            | "uint16"
            | "uint24"
            | "uint32"
            | "uint128"
            | "uint160"
            | "uint256"
            | "memory"
            | "storage"
            | "calldata"
            | "payable"
            | "public"
            | "private"
            | "external"
            | "internal"
            | "virtual"
            | "override"
            | "returns"
            | "return"
            | "if"
            | "else"
            | "for"
            | "while"
            | "new"
            | "is"
            | "contract"
            | "interface"
            | "library"
            | "struct"
            | "enum"
            | "error"
            | "event"
            | "function"
            | "modifier"
    )
}

/// Missing-type completion is intentionally disabled.
/// The slicer must not append definitions just to satisfy compilation.
pub async fn complete_missing_code<'a, G: SemanticGraphAdapter>(
    _slicer: &SemanticSlicer<'a, G>,
    slice_code: &str,
    _source_code: &str,
    _target_function: &str,
) -> Result<String, Box<dyn std::error::Error>> {
    let mut log_file = OpenOptions::new()
        .create(true)
        .append(true)
        .open("analysis.log")?;

    writeln!(log_file, "\n{}", "=".repeat(80))?;
    writeln!(log_file, "=== STARTING CODE COMPLETION (MISSING TYPES) ===")?;
    writeln!(log_file, "{}\n", "=".repeat(80))?;

    // 步骤 1: 检测缺失的类型
    let missing_types = detect_missing_types(slice_code);
    writeln!(
        log_file,
        "📋 Detected {} missing types: {:?}",
        missing_types.len(),
        missing_types
    )?;

    if missing_types.is_empty() {
        writeln!(log_file, "✅ No missing types detected, code is complete")?;
        return Ok(slice_code.to_string());
    }

    writeln!(
        log_file,
        "🔒 Missing-type completion disabled; unresolved types are reported but not appended"
    )?;
    writeln!(
        log_file,
        "⚠️  Unresolved missing types: {:?}",
        missing_types
    )?;
    Ok(slice_code.to_string())
}
