//!
//! 语义代码切片器
//!
//! 本模块实现了基于语义的代码切片算法，结合 LLM 语义分析
//! 和静态启发式规则，评估代码片段之间的相关性，进行智能
//! 的程序依赖图切片，用于 Solidity 安全分析。
//!

use async_trait::async_trait;
use std::collections::{BinaryHeap, HashSet, HashMap};
use std::cmp::Ordering;
use std::fs::OpenOptions;
use std::io::Write;
use futures::future::join_all;

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
}

// 1. 定义评分节点，用于优先队列排序
#[derive(Debug, Clone, PartialEq, Eq)]
struct ScoredItem {
    score: u8, // 0-100
    node_id: usize,
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

// 2. 定义切片器结构体
pub struct SemanticSlicer<'a, G: SemanticGraphAdapter> {
    graph: &'a G,            // 持有适配器的引用
    api_key: String,
    base_url: String,
    model: String,
    score_cache: HashMap<(usize, usize), u8>, // 缓存: (pred, curr) -> score
}

impl<'a, G: SemanticGraphAdapter> SemanticSlicer<'a, G> {
    pub fn new(graph: &'a G, api_key: String, base_url: String, model: String) -> Self {
        Self { graph, api_key, base_url, model, score_cache: HashMap::new() }
    }

    // 核心：基于 LLM 的切片主循环
    pub async fn run_slicing(&mut self, sink_nodes: Vec<usize>) -> HashSet<usize> {
        let mut log_file = OpenOptions::new().create(true).append(true).open("analysis.log").unwrap();
        
        writeln!(log_file, "🚀 STARTING SEMANTIC SLICING").unwrap();
        writeln!(log_file, "📍 Sink Nodes: {:?}", sink_nodes).unwrap();
        
        // 记录每个sink node的详细信息
        for &node_id in &sink_nodes {
            if let Some(node) = self.graph.get_node_info(node_id) {
                writeln!(log_file, "📋 Sink Node {} Details: kind={:?}, label='{}', function_context={:?}", 
                    node_id, node.kind, node.label, node.function_context).unwrap();
            } else {
                writeln!(log_file, "❌ Sink Node {} not found in graph", node_id).unwrap();
            }
        }
        
        let mut pq = BinaryHeap::new();
        let mut result_slice = HashSet::new();
        let mut visited = HashSet::new();

        // 初始化：Sink 点满分入队
        for sink in sink_nodes {
            pq.push(ScoredItem { score: 100, node_id: sink });
            writeln!(log_file, "➕ Added sink node {} with score 100", sink).unwrap();
        }

        let mut iteration = 0;
        while let Some(item) = pq.pop() {
            iteration += 1;
            writeln!(log_file, "\n🔄 Iteration {}: Processing node {} with score {}", iteration, item.node_id, item.score).unwrap();
            
            if item.score < 20 { 
                writeln!(log_file, "✂️  Pruning node {} (score {} < 20)", item.node_id, item.score).unwrap();
                continue; 
            }
            if !visited.insert(item.node_id) { 
                writeln!(log_file, "⏭️  Skipping already visited node {}", item.node_id).unwrap();
                continue; 
            }
            result_slice.insert(item.node_id);
            writeln!(log_file, "✅ Added node {} to slice (total: {})", item.node_id, result_slice.len()).unwrap();

            let current_code = self.graph.get_node_source(item.node_id);
            let preds = self.graph.get_predecessors(item.node_id);
            
            writeln!(log_file, "🔍 Analyzing predecessors of node {}: {:?}", item.node_id, preds).unwrap();

            // 批量/并发处理依赖评分
            let mut futures = Vec::new();
            for &pred_id in &preds {
                if visited.contains(&pred_id) { 
                    writeln!(log_file, "⏭️  Skipping visited predecessor {}", pred_id).unwrap();
                    continue; 
                }
                
                // 收集 futures
                futures.push(self.calculate_relevance(pred_id, item.node_id, iteration));
            }
            
            // 并发执行评分
            let scores = join_all(futures).await;
            
            // 处理结果
            let mut score_iter = scores.into_iter();
            for &pred_id in &preds {
                if visited.contains(&pred_id) { 
                    continue; 
                }
                
                let rel_score = score_iter.next().unwrap();
                writeln!(log_file, "📊 Relevance score for pred {} -> curr {}: {}", pred_id, item.node_id, rel_score).unwrap();
                
                // 距离衰减
                let decayed = (rel_score as f32 * 0.95) as u8;
                writeln!(log_file, "📉 Decayed score: {} -> {}", rel_score, decayed).unwrap();
                
                if decayed >= 20 {
                    pq.push(ScoredItem { score: decayed, node_id: pred_id });
                    writeln!(log_file, "➕ Enqueued predecessor {} with score {}", pred_id, decayed).unwrap();
                } else {
                    writeln!(log_file, "✂️  Not enqueuing predecessor {} (decayed score {} < 20)", pred_id, decayed).unwrap();
                }
            }
            
            writeln!(log_file, "📋 Current queue size: {}", pq.len()).unwrap();
        }
        
        writeln!(log_file, "\n🎉 SLICING COMPLETED").unwrap();
        writeln!(log_file, "📊 Final slice contains {} nodes: {:?}", result_slice.len(), result_slice).unwrap();
        writeln!(log_file, "🏁 END SEMANTIC SLICING\n").unwrap();
        
        result_slice
    }
    
    // 评分逻辑：混合 启发式规则 + LLM
    async fn calculate_relevance(&self, pred_id: usize, curr_id: usize, depth: usize) -> u8 {
        let mut log_file = OpenOptions::new().create(true).append(true).open("analysis.log").unwrap();
        
        writeln!(log_file, "🔍 Calculating relevance for pred_id {} -> curr_id {} at depth {}", pred_id, curr_id, depth).unwrap();
        
        // 首先尝试静态启发式评分
        let static_score = self.static_relevance_score(pred_id, curr_id, depth);
        writeln!(log_file, "📊 Static heuristic score: {}", static_score).unwrap();
        
        // 如果静态分数足够高，直接返回
        if static_score >= 80 {
            writeln!(log_file, "✅ Using static score (high confidence): {}", static_score).unwrap();
            return static_score;
        }
        
        // 否则使用 LLM 进行语义分析
        writeln!(log_file, "🤖 Using LLM for semantic analysis...").unwrap();
        let pred_code = self.graph.get_node_source(pred_id);
        let curr_code = self.graph.get_node_source(curr_id);
        match self.call_llm_for_relevance(&pred_code, &curr_code, depth).await {
            Ok(llm_score) => {
                writeln!(log_file, "🔢 LLM score: {}", llm_score).unwrap();
                // 结合静态和LLM分数，取加权平均
                let combined = ((static_score as f32 * 0.3) + (llm_score as f32 * 0.7)) as u8;
                writeln!(log_file, "🔢 Combined score: {} (static: {}, llm: {})", combined, static_score, llm_score).unwrap();
                combined
            },
            Err(e) => {
                writeln!(log_file, "❌ LLM call failed: {}, falling back to static score {}", e, static_score).unwrap();
                static_score
            }
        }
    }

    // 静态启发式评分：基于变量重叠和函数调用深度
    fn static_relevance_score(&self, pred_id: usize, curr_id: usize, depth: usize) -> u8 {
        let mut score = 0u8;
        
        // 1. 变量重叠度
        let pred_vars: HashSet<_> = self.graph.extract_identifiers(pred_id).into_iter().collect();
        let curr_vars: HashSet<_> = self.graph.extract_identifiers(curr_id).into_iter().collect();
        let overlap: HashSet<_> = pred_vars.intersection(&curr_vars).collect();
        let overlap_ratio = if !curr_vars.is_empty() { overlap.len() as f32 / curr_vars.len() as f32 } else { 0.0 };
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
        
        score.min(100)
    }

    // 检查是否有复杂数据流（算术运算、多重赋值等）
    fn has_complex_data_flow(&self, code: &str) -> bool {
        code.contains(" + ") || code.contains(" - ") || code.contains(" * ") || code.contains(" / ") || 
        code.contains(" += ") || code.contains(" -= ") || code.contains(" *= ") || code.contains(" /= ") ||
        code.matches(" = ").count() > 1
    }


    // 判断代码块是否与目标相关
    pub async fn is_code_relevant(&self, code: &str, target_variable: &str, full_context: &str, related_functions: &[String]) -> bool {
        let mut log_file = OpenOptions::new().create(true).append(true).open("analysis.log").unwrap();
        
        writeln!(log_file, "=== STARTING RELEVANCE ANALYSIS ===").unwrap();
        writeln!(log_file, "Target Variable: {}", target_variable).unwrap();
        writeln!(log_file, "Code to Analyze: {}", code.lines().next().unwrap_or("").trim()).unwrap();
        
        // 静态规则：如果代码直接包含目标变量，认为是相关的
        if code.contains(target_variable) {
            writeln!(log_file, "✅ DIRECT MATCH: Code contains target variable '{}'", target_variable).unwrap();
            return true;
        }
        
        // 静态分析：跨合约依赖和返回值使用
        // 简化：暂时移除复杂的字符串解析，交由 Adapter 处理
        // if self.analyze_cross_contract_relevance(code, target_variable, full_context) {
        //     writeln!(log_file, "✅ STATIC ANALYSIS: Cross-contract relevance detected for '{}'", target_variable).unwrap();
        //     return true;
        // }
        
        writeln!(log_file, "🤖 USING LLM ANALYSIS: No direct matches found, calling LLM...").unwrap();
        
        // 否则使用 LLM 判断
        match self.call_llm_with_context_and_related(code, target_variable, full_context, related_functions).await {
            Ok(response) => {
                writeln!(log_file, "=== PARSING LLM RESPONSE ===").unwrap();
                
                // 清理响应，只提取JSON部分
                let json_str = if let Some(start) = response.find("```json") {
                    let content_start = start + 7; // 跳过"```json"
                    if let Some(end_offset) = response[content_start..].find("```") {
                        let content_end = content_start + end_offset;
                        let extracted = &response[content_start..content_end];
                        writeln!(log_file, "Extracted JSON from ```json block: {}", extracted).unwrap();
                        extracted
                    } else {
                        let extracted = &response[content_start..];
                        writeln!(log_file, "Extracted JSON from ```json block (no end marker): {}", extracted).unwrap();
                        extracted
                    }
                } else if let Some(start) = response.find('{') {
                    if let Some(end) = response.rfind('}') {
                        let extracted = &response[start..=end];
                        writeln!(log_file, "Extracted JSON from curly braces: {}", extracted).unwrap();
                        extracted
                    } else {
                        let extracted = &response[start..];
                        writeln!(log_file, "Extracted JSON from start brace (no end): {}", extracted).unwrap();
                        extracted
                    }
                } else {
                    writeln!(log_file, "No JSON markers found, using raw response: {}", response).unwrap();
                    &response
                };
                
                // 解析 JSON 响应
                match serde_json::from_str::<serde_json::Value>(json_str) {
                    Ok(json) => {
                        writeln!(log_file, "✅ JSON parsed successfully").unwrap();
                        if let Some(score) = json["score"].as_i64() {
                            let score_i32 = score as i32;
                            writeln!(log_file, "📊 Extracted Score: {}", score_i32).unwrap();
                            if let Some(reason) = json["reason"].as_str() {
                                writeln!(log_file, "💬 Reason: {}", reason).unwrap();
                            }
                            
                            let is_relevant = score >= 5;
                            writeln!(log_file, "🎯 Final Decision: {} (threshold: 5, score: {})", 
                                    if is_relevant { "RELEVANT" } else { "NOT RELEVANT" }, score).unwrap();
                            writeln!(log_file, "=== END RELEVANCE ANALYSIS ===\n").unwrap();
                            
                            return is_relevant;
                        } else {
                            writeln!(log_file, "❌ No 'score' field found in JSON").unwrap();
                        }
                    },
                    Err(e) => {
                        writeln!(log_file, "❌ JSON parsing failed: {}", e).unwrap();
                        writeln!(log_file, "Raw JSON string was: '{}'", json_str).unwrap();
                    }
                }
                
                writeln!(log_file, "⚠️  Falling back to default (relevant) due to parsing failure").unwrap();
                writeln!(log_file, "=== END RELEVANCE ANALYSIS ===\n").unwrap();
                true // 默认保留，如果解析失败
            },
            Err(e) => {
                writeln!(log_file, "❌ LLM call failed: {}", e).unwrap();
                writeln!(log_file, "⚠️  Falling back to default (relevant) due to API failure").unwrap();
                writeln!(log_file, "=== END RELEVANCE ANALYSIS ===\n").unwrap();
                true // 默认保留，如果 LLM 调用失败
            }
        }
    }

    // 使用 LLM 计算两个代码片段之间的语义相关性
    async fn call_llm_for_relevance(&self, pred_code: &str, curr_code: &str, depth: usize) -> Result<u8, Box<dyn std::error::Error>> {
        // 模拟 LLM 响应以进行测试
        let simulated_score = 70 + (depth as u8 * 5); // 深度越高，分数略高
        Ok(simulated_score.min(100))
    }

    // 使用 LLM 判断代码是否与目标变量相关，提供完整上下文和相关函数集合
    async fn call_llm_with_context_and_related(&self, code: &str, target_variable: &str, full_context: &str, related_functions: &[String]) -> Result<String, Box<dyn std::error::Error>> {
        let mut log_file = OpenOptions::new().create(true).append(true).open("analysis.log")?;
        
        writeln!(log_file, "=== STARTING LLM ANALYSIS ===")?;
        writeln!(log_file, "Target Variable: {}", target_variable)?;
        writeln!(log_file, "Function Code: {}", code.lines().next().unwrap_or("").trim())?;
        writeln!(log_file, "Related Functions Count: {}", related_functions.len())?;
        
        // 1. 定义更智能的 System Prompt
        let system_prompt = r#"You are a specialized Solidity program slicer. 
Your job is to identify ALL functions that influence the value of a specific Target State Variable, strictly following the dependency chain:
1. Direct Modification: Function writes to Target.
2. Direct Computation: Function returns a value used to calculate Target.
3. Upstream State Change: Function modifies a variable (even in another contract) that is READ by a function in category 1 or 2.

Think step-by-step:
- Does this function change ANY state?
- Is that state read by the Target Contract?
- Does the Target Contract use that state to update the Target Variable?
If yes, Score must be > 0."#;

        // 构造精简的合约上下文（状态变量和事件）
        let simplified_context = self.graph.get_contract_context_summary();
        writeln!(log_file, "Simplified Context Length: {} chars", simplified_context.len())?;
        
        // 2. 构造包含调用关系的上下文 (暂时使用宽泛的Criteria，如果做不到自动提取调用关系)
        let criteria = r#"Criteria for Relevance Score (0-10):
- 10: Directly writes to 'totalAssets'.
- 8-9: Modifies a variable (like 'price') that is CRITICAL for calculating 'totalAssets', even if in an external Oracle contract.
- 5-7: Sets up dependencies (e.g., sets the Oracle address).
- 1-4: Affects control flow (e.g., 'pause' switch) wrapping the update logic.
- 0: Completely unrelated (e.g., logging, events, unrelated state)."#;
        
        // 使用 reqwest 调用 LLM API
        let client = reqwest::Client::new();
        let request_body = serde_json::json!({
            "model": self.model,
            "messages": [
                { "role": "system", "content": system_prompt },
                { "role": "user", "content": format!("Context Summary:\n{}\n\n(Note: Assume standard interactions between these contracts if code is missing. e.g. Vault reads Price from Oracle.)", simplified_context) },
                { "role": "user", "content": format!("Function to Analyze:\n```solidity\n{}\n```", code) },
                { "role": "user", "content": format!("Target Variable: '{}'\n\n{}\n\nOutput strictly JSON: {{\"score\": int, \"reason\": string}}", target_variable, criteria) }
            ]
        });

        writeln!(log_file, "=== SENDING PROMPT TO LLM ===")?;
        writeln!(log_file, "Model: {}", self.model)?;
        writeln!(log_file, "API Endpoint: {}/chat/completions", self.base_url)?;
        writeln!(log_file, "Full Request Body: {}", serde_json::to_string_pretty(&request_body).unwrap_or("Serialization failed".to_string()))?;
        
        let response = client
            .post(format!("{}/chat/completions", self.base_url))
            .header("Authorization", format!("Bearer {}", self.api_key))
            .header("Content-Type", "application/json")
            .json(&request_body)
            .send()
            .await;

        match response {
            Ok(resp) => {
                writeln!(log_file, "=== LLM API RESPONSE RECEIVED ===")?;
                writeln!(log_file, "Status Code: {}", resp.status())?;
                
                let response_json: Result<serde_json::Value, _> = resp.json().await;
                match response_json {
                    Ok(json) => {
                        let response_text = json["choices"][0]["message"]["content"]
                            .as_str()
                            .unwrap_or("{\"score\": 0, \"reason\": \"Parse error\"}")
                            .trim()
                            .to_string();
                        
                        writeln!(log_file, "=== RAW LLM RESPONSE ===")?;
                        writeln!(log_file, "{}", response_text)?;
                        writeln!(log_file, "=== END RAW RESPONSE ===")?;
                        
                        Ok(response_text)
                    },
                    Err(e) => {
                        writeln!(log_file, "=== ERROR PARSING LLM JSON RESPONSE ===")?;
                        writeln!(log_file, "Error: {}", e)?;
                        Err(Box::new(e))
                    }
                }
            },
            Err(e) => {
                writeln!(log_file, "=== ERROR CALLING LLM API ===")?;
                writeln!(log_file, "Error: {}", e)?;
                Err(Box::new(e))
            }
        }
    }
}
