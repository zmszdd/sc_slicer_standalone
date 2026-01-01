//! 噪音削减模块 (Noise Reduction)
//! 
//! 这个模块实现了一系列"外科手术级"的代码净化策略，
//! 旨在将切片结果中的无效噪音从 ~60% 降低到接近 0%。
//! 
//! ## 核心优化策略
//! 
//! 1. **标准库截肢** (Stdlib Stubbing)
//!    - 检测 OpenZeppelin、Solady、Forge-std 等标准库
//!    - 将完整实现替换为 `{ /* stdlib: collapsed */ }`
//! 
//! 2. **ASCII 艺术清洗** (Visual Noise Cleanup)  
//!    - 删除连续 3+ 行的注释块
//!    - 移除包含 ASCII 绘图字符的注释
//! 
//! 3. **类型摇树优化** (Type Tree-Shaking)
//!    - 扫描保留函数中的类型引用
//!    - 删除未被引用的 struct/enum 定义
//!    - 强制删除 Foundry 内部类型
//! 
//! 4. **依赖库去重** (Lib Deduplication)
//!    - 检测 `Math_0`, `Math_1`, `Math_2` 等同名异构库
//!    - 保留被调用的版本,删除未引用的版本
//! 
//! 5. **调用链聚焦** (Call Chain Focus)
//!    - 严格的调用链分析
//!    - 只保留 PoC 路径触达的函数

use std::collections::{HashMap, HashSet};
use regex::Regex;

/// 标准库模式配置
pub struct StdlibConfig {
    /// OpenZeppelin 库模式
    pub openzeppelin_patterns: Vec<&'static str>,
    /// Solady 库模式
    pub solady_patterns: Vec<&'static str>,
    /// Forge-std 库模式
    pub forge_std_patterns: Vec<&'static str>,
    /// 其他通用库模式
    pub common_patterns: Vec<&'static str>,
}

impl Default for StdlibConfig {
    fn default() -> Self {
        Self {
            openzeppelin_patterns: vec![
                "Address",
                "SafeMath",
                "SafeERC20",
                "ReentrancyGuard",
                "Ownable",
                "Pausable",
                "ERC20",
                "ERC721",
                "ERC1155",
                "AccessControl",
                "Initializable",
            ],
            solady_patterns: vec![
                "FixedPointMathLib",
                "SafeTransferLib",
                "LibString",
                "LibBit",
                "MerkleProofLib",
            ],
            forge_std_patterns: vec![
                "Test",
                "StdCheats",
                "StdAssertions",
                "StdUtils",
                "Vm",
                "console",
                "Script",
            ],
            common_patterns: vec![
                "Math",
                "SignedMath",
                "Strings",
                "Arrays",
                "Context",
                "Counters",
            ],
        }
    }
}

impl StdlibConfig {
    /// 检查合约名是否是标准库
    pub fn is_stdlib(&self, contract_name: &str) -> bool {
        // 精确匹配
        if self.openzeppelin_patterns.iter().any(|&pat| contract_name == pat)
            || self.solady_patterns.iter().any(|&pat| contract_name == pat)
            || self.forge_std_patterns.iter().any(|&pat| contract_name == pat)
            || self.common_patterns.iter().any(|&pat| contract_name == pat)
        {
            return true;
        }

        // 模糊匹配：检查是否包含标准库标识
        contract_name.ends_with("Lib") 
            || contract_name.starts_with("ERC")
            || contract_name.starts_with("I")  // 接口
            || contract_name.contains("Utils")
            || contract_name.contains("Helper")
    }

    /// 生成存根代码
    pub fn generate_stub(&self, contract_type: &str, contract_name: &str) -> String {
        format!("{} {} {{ /* stdlib: collapsed */ }}", contract_type, contract_name)
    }
}

/// Foundry 内部类型黑名单
pub const FOUNDRY_BLACKLIST: &[&str] = &[
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
    // Cheatcodes 相关
    "VmSafe", "Vm_", "StdStorage",
];

/// ASCII 艺术字符集
pub const ASCII_ART_CHARS: &str = "▲▼◄►│┌┐└┘├┤┬┴┼─═║╔╗╚╝╠╣╦╩╬┄┅┆┇┈┉┊┋";

/// 注释清洗器
pub struct CommentCleaner {
    /// 删除连续注释的最小行数阈值
    pub consecutive_comment_threshold: usize,
    /// 是否保留函数体内的注释
    pub preserve_inline_comments: bool,
}

impl Default for CommentCleaner {
    fn default() -> Self {
        Self {
            consecutive_comment_threshold: 3,
            preserve_inline_comments: true,
        }
    }
}

impl CommentCleaner {
    /// 清洗单行注释
    pub fn clean_line(&self, line: &str, context: &CleanContext) -> Option<String> {
        let trimmed = line.trim();

        // 1. 检测并删除 ASCII 艺术
        if self.is_ascii_art(trimmed) {
            return None;
        }

        // 2. 删除文件头注释（SPDX、License等）
        if context.is_file_header && trimmed.starts_with("//") {
            if self.is_header_noise(trimmed) {
                return None;
            }
        }

        // 3. 删除库文件中的文档注释
        if context.is_in_library && !context.in_function_body {
            if trimmed.starts_with("///") || trimmed.starts_with("/**") {
                return None;
            }
        }

        // 4. 保留函数体内的逻辑注释（可选）
        if context.in_function_body && self.preserve_inline_comments {
            if trimmed.starts_with("//") && self.is_logic_comment(trimmed) {
                return Some(line.to_string());
            }
        }

        // 5. 删除纯注释行（不在函数体内）
        if !context.in_function_body && (trimmed.starts_with("//") || trimmed.starts_with("/*")) {
            return None;
        }

        Some(line.to_string())
    }

    /// 检测是否包含 ASCII 艺术
    fn is_ascii_art(&self, line: &str) -> bool {
        line.chars().any(|c| ASCII_ART_CHARS.contains(c))
    }

    /// 检测是否是文件头噪音
    fn is_header_noise(&self, line: &str) -> bool {
        let patterns = [
            "// SPDX-",
            "// License",
            "// pragma",
            "// solc",
            "// Author:",
            "// Title:",
            "// @notice",
            "// @dev",
        ];
        patterns.iter().any(|&pat| line.starts_with(pat))
    }

    /// 检测是否是逻辑注释（值得保留）
    fn is_logic_comment(&self, line: &str) -> bool {
        let useful_patterns = [
            "// FIXME",
            "// TODO",
            "// HACK",
            "// BUG",
            "// WARNING",
            "// CRITICAL",
            "// step",
            "// check",
            "// 步骤",
            "// 检查",
        ];
        useful_patterns.iter().any(|&pat| line.to_lowercase().contains(&pat.to_lowercase()))
    }

    /// 批量清洗代码块
    pub fn clean_block(&self, lines: &[&str], context: &CleanContext) -> Vec<String> {
        let mut result = Vec::new();
        let mut consecutive_comments = 0;
        let mut pending_comments = Vec::new();

        for line in lines {
            let trimmed = line.trim();
            
            // 更新上下文（追踪是否在函数体内）
            let mut updated_context = context.clone();
            updated_context.update_with_line(trimmed);

            if trimmed.starts_with("//") || trimmed.starts_with("/*") {
                consecutive_comments += 1;
                pending_comments.push(*line);
            } else {
                // 非注释行

                // 检查是否需要删除连续注释
                if consecutive_comments >= self.consecutive_comment_threshold {
                    // 删除所有待处理的注释
                    pending_comments.clear();
                } else {
                    // 保留（部分）注释
                    for comment_line in &pending_comments {
                        if let Some(cleaned) = self.clean_line(comment_line, &updated_context) {
                            result.push(cleaned);
                        }
                    }
                }

                // 重置计数器
                consecutive_comments = 0;
                pending_comments.clear();

                // 添加当前行
                if !trimmed.is_empty() {
                    result.push(line.to_string());
                }
            }
        }

        result
    }
}

/// 清洗上下文
#[derive(Clone)]
pub struct CleanContext {
    /// 是否在文件头部（前 50 行）
    pub is_file_header: bool,
    /// 是否在库文件中
    pub is_in_library: bool,
    /// 是否在函数体内
    pub in_function_body: bool,
    /// 当前大括号深度
    pub brace_depth: i32,
}

impl Default for CleanContext {
    fn default() -> Self {
        Self {
            is_file_header: true,
            is_in_library: false,
            in_function_body: false,
            brace_depth: 0,
        }
    }
}

impl CleanContext {
    /// 根据代码行更新上下文
    pub fn update_with_line(&mut self, line: &str) {
        // 更新大括号深度
        self.brace_depth += line.matches('{').count() as i32;
        self.brace_depth -= line.matches('}').count() as i32;

        // 检测函数开始
        if line.starts_with("function ") || line.starts_with("constructor") {
            if line.contains('{') {
                self.in_function_body = true;
            }
        }

        // 检测函数结束
        if self.brace_depth <= 0 {
            self.in_function_body = false;
            self.brace_depth = 0;
        }

        // 检测库声明
        if line.starts_with("library ") {
            self.is_in_library = true;
        }
    }
}

/// 类型摇树器 (Type Tree-Shaker)
pub struct TypeTreeShaker {
    /// 已使用的类型集合
    pub used_types: HashSet<String>,
    /// Foundry 黑名单
    pub foundry_blacklist: HashSet<String>,
}

impl Default for TypeTreeShaker {
    fn default() -> Self {
        Self {
            used_types: HashSet::new(),
            foundry_blacklist: FOUNDRY_BLACKLIST.iter().map(|s| s.to_string()).collect(),
        }
    }
}

impl TypeTreeShaker {
    /// 从保留的代码中提取所有使用的类型
    pub fn extract_used_types(&mut self, code_blocks: &[String]) {
        for block in code_blocks {
            for token in self.tokenize(block) {
                if self.is_valid_type_name(&token) {
                    self.used_types.insert(token);
                }
            }
        }
    }

    /// 简单的 token 化（按非字母数字字符分割）
    fn tokenize(&self, code: &str) -> Vec<String> {
        let mut tokens = Vec::new();
        let mut current_token = String::new();

        for ch in code.chars() {
            if ch.is_alphanumeric() || ch == '_' {
                current_token.push(ch);
            } else {
                if !current_token.is_empty() {
                    tokens.push(current_token.clone());
                    current_token.clear();
                }
            }
        }

        if !current_token.is_empty() {
            tokens.push(current_token);
        }

        tokens
    }

    /// 检查是否是有效的类型名（首字母大写）
    fn is_valid_type_name(&self, token: &str) -> bool {
        if token.is_empty() {
            return false;
        }
        
        // 类型名通常首字母大写
        token.chars().next().unwrap().is_uppercase()
    }

    /// 检查类型是否应该被保留
    pub fn should_keep_type(&self, type_name: &str) -> bool {
        // 1. Foundry 黑名单：强制删除
        if self.foundry_blacklist.contains(type_name) {
            return false;
        }

        // 2. 引用检查：被使用的类型保留
        self.used_types.contains(type_name)
    }

    /// 过滤类型定义块
    pub fn filter_type_definitions(&self, blocks: Vec<String>) -> (Vec<String>, Vec<String>) {
        let mut kept = Vec::new();
        let mut removed = Vec::new();

        for block in blocks {
            let first_line = block.lines().next().unwrap_or("").trim();
            
            if first_line.starts_with("struct ") 
                || first_line.starts_with("enum ") 
                || first_line.starts_with("type ") 
            {
                let type_name = self.extract_type_name(first_line);
                
                if self.should_keep_type(&type_name) {
                    kept.push(block);
                } else {
                    removed.push(type_name);
                }
            } else {
                // 非类型定义，保留
                kept.push(block);
            }
        }

        (kept, removed)
    }

    /// 从定义行中提取类型名
    fn extract_type_name(&self, line: &str) -> String {
        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.len() >= 2 {
            parts[1].trim_end_matches('{').trim().to_string()
        } else {
            String::new()
        }
    }
}

/// 依赖库去重器
pub struct LibraryDeduplicator {
    /// 库名 -> 版本列表 (例如: "Math" -> ["Math_0", "Math_1", "Math_2"])
    pub library_versions: HashMap<String, Vec<String>>,
    /// 被调用的库版本
    pub called_versions: HashSet<String>,
}

impl Default for LibraryDeduplicator {
    fn default() -> Self {
        Self {
            library_versions: HashMap::new(),
            called_versions: HashSet::new(),
        }
    }
}

impl LibraryDeduplicator {
    /// 检测同名异构库
    pub fn detect_versioned_libraries(&mut self, code_blocks: &[String]) {
        let version_pattern = Regex::new(r"^library\s+(\w+?)_(\d+)\s*\{").unwrap();

        for block in code_blocks {
            if let Some(first_line) = block.lines().next() {
                if let Some(caps) = version_pattern.captures(first_line) {
                    let base_name = caps.get(1).unwrap().as_str().to_string();
                    let full_name = format!("{}_{}", base_name, caps.get(2).unwrap().as_str());
                    
                    self.library_versions
                        .entry(base_name)
                        .or_insert_with(Vec::new)
                        .push(full_name);
                }
            }
        }
    }

    /// 扫描调用记录
    pub fn scan_library_calls(&mut self, code_blocks: &[String]) {
        for block in code_blocks {
            // 查找库调用模式：LibraryName.method(...)
            let call_pattern = Regex::new(r"\b(\w+_\d+)\.").unwrap();
            
            for caps in call_pattern.captures_iter(block) {
                let lib_name = caps.get(1).unwrap().as_str();
                self.called_versions.insert(lib_name.to_string());
            }
        }
    }

    /// 过滤未使用的库版本
    pub fn filter_unused_versions(&self, blocks: Vec<String>) -> (Vec<String>, Vec<String>) {
        let mut kept = Vec::new();
        let mut removed = Vec::new();

        for block in blocks {
            let first_line = block.lines().next().unwrap_or("").trim();
            
            if first_line.starts_with("library ") {
                let lib_name = first_line
                    .split_whitespace()
                    .nth(1)
                    .unwrap_or("")
                    .trim_end_matches('{')
                    .trim();
                
                // 检查是否是版本化的库
                if lib_name.contains('_') && lib_name.chars().last().unwrap().is_numeric() {
                    // 是版本化库：检查是否被调用
                    if self.called_versions.contains(lib_name) {
                        kept.push(block);
                    } else {
                        removed.push(lib_name.to_string());
                    }
                } else {
                    // 非版本化库：保留
                    kept.push(block);
                }
            } else {
                kept.push(block);
            }
        }

        (kept, removed)
    }
}

/// 噪音削减管道（主入口）
pub struct NoiseReductionPipeline {
    pub stdlib_config: StdlibConfig,
    pub comment_cleaner: CommentCleaner,
    pub type_shaker: TypeTreeShaker,
    pub lib_deduplicator: LibraryDeduplicator,
}

impl Default for NoiseReductionPipeline {
    fn default() -> Self {
        Self {
            stdlib_config: StdlibConfig::default(),
            comment_cleaner: CommentCleaner::default(),
            type_shaker: TypeTreeShaker::default(),
            lib_deduplicator: LibraryDeduplicator::default(),
        }
    }
}

impl NoiseReductionPipeline {
    /// 执行完整的噪音削减流程
    pub fn reduce(&mut self, code_blocks: Vec<String>) -> NoiseReductionResult {
        let mut stats = NoiseReductionStats::default();
        stats.original_blocks = code_blocks.len();

        // 🔥 阶段 1: 标准库存根化
        println!("📚 [Phase 1/5] Stubbing standard libraries...");
        let (stubbed_blocks, stdlib_count) = self.stub_stdlib(code_blocks);
        stats.stdlib_stubbed = stdlib_count;

        // 🔥 阶段 2: 注释清洗
        println!("✂️  [Phase 2/5] Cleaning aggressive comments...");
        let (cleaned_blocks, comment_lines) = self.clean_comments(stubbed_blocks);
        stats.comment_lines_removed = comment_lines;

        // 🔥 阶段 3: 类型摇树
        println!("🌳 [Phase 3/5] Type tree-shaking...");
        let (shaken_blocks, removed_types) = self.shake_types(cleaned_blocks);
        stats.types_removed = removed_types.len();

        // 🔥 阶段 4: 库去重
        println!("🔄 [Phase 4/5] Library deduplication...");
        let (deduped_blocks, removed_libs) = self.deduplicate_libraries(shaken_blocks);
        stats.libs_deduped = removed_libs.len();

        // 🔥 阶段 5: 空行压缩
        println!("📦 [Phase 5/5] Compressing blank lines...");
        let final_blocks = self.compress_blank_lines(deduped_blocks);
        stats.final_blocks = final_blocks.len();

        NoiseReductionResult {
            code_blocks: final_blocks,
            stats,
        }
    }

    /// 阶段 1: 标准库存根化
    fn stub_stdlib(&self, blocks: Vec<String>) -> (Vec<String>, usize) {
        let mut result = Vec::new();
        let mut stub_count = 0;

        for block in blocks {
            let first_line = block.lines().next().unwrap_or("").trim();
            
            if first_line.starts_with("library ") || first_line.starts_with("contract ") {
                let contract_type = if first_line.starts_with("library ") { "library" } else { "contract" };
                let name = first_line
                    .split_whitespace()
                    .nth(1)
                    .unwrap_or("")
                    .trim_end_matches('{')
                    .trim();
                
                if self.stdlib_config.is_stdlib(name) {
                    result.push(self.stdlib_config.generate_stub(contract_type, name));
                    stub_count += 1;
                    println!("  📚 Stubbed: {}", name);
                } else {
                    result.push(block);
                }
            } else {
                result.push(block);
            }
        }

        (result, stub_count)
    }

    /// 阶段 2: 注释清洗
    fn clean_comments(&self, blocks: Vec<String>) -> (Vec<String>, usize) {
        let mut result = Vec::new();
        let mut total_removed = 0;

        for block in blocks {
            let lines: Vec<&str> = block.lines().collect();
            let original_count = lines.len();
            
            // 判断是否是库文件
            let first_line = lines.first().map(|l| l.trim()).unwrap_or("");
            let is_library = first_line.starts_with("library ");
            
            let context = CleanContext {
                is_file_header: false, // 在代码块级别，已经不是文件头了
                is_in_library: is_library,
                in_function_body: false,
                brace_depth: 0,
            };
            
            let cleaned_lines = self.comment_cleaner.clean_block(&lines, &context);
            let removed = original_count - cleaned_lines.len();
            total_removed += removed;
            
            if !cleaned_lines.is_empty() {
                result.push(cleaned_lines.join("\n"));
            }
        }

        (result, total_removed)
    }

    /// 阶段 3: 类型摇树
    fn shake_types(&mut self, blocks: Vec<String>) -> (Vec<String>, Vec<String>) {
        // 先提取所有使用的类型
        self.type_shaker.extract_used_types(&blocks);
        
        // 过滤类型定义
        let (kept, removed) = self.type_shaker.filter_type_definitions(blocks);
        
        for type_name in &removed {
            println!("  🌳 Removed type: {}", type_name);
        }
        
        (kept, removed)
    }

    /// 阶段 4: 库去重
    fn deduplicate_libraries(&mut self, blocks: Vec<String>) -> (Vec<String>, Vec<String>) {
        // 检测版本化库
        self.lib_deduplicator.detect_versioned_libraries(&blocks);
        
        // 扫描调用
        self.lib_deduplicator.scan_library_calls(&blocks);
        
        // 过滤未使用的版本
        let (kept, removed) = self.lib_deduplicator.filter_unused_versions(blocks);
        
        for lib_name in &removed {
            println!("  🔄 Removed duplicate: {}", lib_name);
        }
        
        (kept, removed)
    }

    /// 阶段 5: 压缩空行
    fn compress_blank_lines(&self, blocks: Vec<String>) -> Vec<String> {
        blocks
            .into_iter()
            .map(|block| {
                let lines: Vec<&str> = block.lines().collect();
                let mut result = Vec::new();
                let mut consecutive_blank = 0;

                for line in lines {
                    if line.trim().is_empty() {
                        consecutive_blank += 1;
                        if consecutive_blank <= 1 {
                            result.push(line.to_string());
                        }
                    } else {
                        consecutive_blank = 0;
                        result.push(line.to_string());
                    }
                }

                result.join("\n")
            })
            .collect()
    }
}

/// 噪音削减结果
pub struct NoiseReductionResult {
    pub code_blocks: Vec<String>,
    pub stats: NoiseReductionStats,
}

/// 噪音削减统计
#[derive(Default)]
pub struct NoiseReductionStats {
    pub original_blocks: usize,
    pub stdlib_stubbed: usize,
    pub comment_lines_removed: usize,
    pub types_removed: usize,
    pub libs_deduped: usize,
    pub final_blocks: usize,
}

impl NoiseReductionStats {
    pub fn print_summary(&self) {
        println!("\n╔═══════════════════════════════════════════════╗");
        println!("║  Noise Reduction Summary                     ║");
        println!("╠═══════════════════════════════════════════════╣");
        println!("║  Original code blocks:      {:>6}           ║", self.original_blocks);
        println!("║  Standard libs stubbed:     {:>6}           ║", self.stdlib_stubbed);
        println!("║  Comment lines removed:     {:>6}           ║", self.comment_lines_removed);
        println!("║  Types removed:             {:>6}           ║", self.types_removed);
        println!("║  Libraries deduped:         {:>6}           ║", self.libs_deduped);
        println!("║  Final code blocks:         {:>6}           ║", self.final_blocks);
        println!("╠═══════════════════════════════════════════════╣");
        
        if self.original_blocks > 0 {
            let reduction_rate = ((self.original_blocks - self.final_blocks) as f64 
                / self.original_blocks as f64) * 100.0;
            println!("║  Noise reduction rate:      {:>5.1}%          ║", reduction_rate);
        }
        
        println!("╚═══════════════════════════════════════════════╝\n");
    }
}
