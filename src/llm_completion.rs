//! LLM辅助代码补全模块
//! 
//! 三阶段智能修复策略：
//! 1. LLM分析识别关键缺失函数（最多3个）
//! 2. AST精确补全关键函数
//! 3. LLM修复使代码可编译

use serde::{Deserialize, Serialize};
use solar_ast::ItemKind;
use solar_interface::Session;

#[derive(Debug, Serialize, Deserialize)]
pub struct LLMRequest {
    pub model: String,
    pub messages: Vec<Message>,
    pub temperature: f32,
    pub max_tokens: usize,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Message {
    pub role: String,
    pub content: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct LLMResponse {
    pub choices: Vec<Choice>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Choice {
    pub message: Message,
}

#[derive(Debug)]
pub struct MissingFunction {
    pub name: String,
    pub contract: String,
    pub priority: usize, // 1=最重要, 2=次要, 3=可选
}

pub struct LLMCompletionPipeline {
    api_key: String,
    base_url: String,
    model: String,
    source_file_path: Option<String>, // 原始源码文件路径，用于AST提取
}

impl LLMCompletionPipeline {
    pub fn new() -> Result<Self, String> {
        let api_key = std::env::var("OPENAI_API_KEY")
            .unwrap_or_else(|_| "sk-4d65d403d3a14e10b027c1cd65f3da77".to_string());
        
        if api_key.is_empty() {
            return Err("API密钥未设置".to_string());
        }

        Ok(Self {
            api_key,
            base_url: std::env::var("OPENAI_BASE_URL")
                .unwrap_or_else(|_| "https://api.deepseek.com".to_string()),
            model: std::env::var("LLM_MODEL")
                .unwrap_or_else(|_| "deepseek-chat".to_string()),
            source_file_path: None,
        })
    }

    pub fn with_source_file(mut self, path: String) -> Self {
        self.source_file_path = Some(path);
        self
    }

    /// 阶段1: LLM分析识别关键缺失函数
    pub fn analyze_missing_functions(&self, sliced_code: &str) -> Result<Vec<MissingFunction>, String> {
        println!("\n� 阶段1: LLM分析识别关键缺失函数...");
        
        let prompt = format!(r#"你是Solidity代码分析专家。分析以下切片后的代码，识别**最关键**的缺失函数定义（最多3个）。

**分析重点**：
1. 测试函数中直接调用但未定义的函数
2. 核心业务逻辑依赖的函数（如计算函数、状态更新函数）
3. 多处引用的工具函数

**输出格式**（JSON）：
```json
[
  {{"name": "<functionName>", "contract": "<ContractName>", "priority": <1-3>}},
  {{"name": "<anotherFunction>", "contract": "<AnotherContract>", "priority": <1-3>}}
]
```

**priority说明**：
- 1: 核心业务逻辑（测试直接依赖）
- 2: 重要辅助函数（核心逻辑间接调用）
- 3: 可选工具函数（可简化实现）

只返回JSON数组，不要其他解释。如果没有关键缺失函数，返回空数组 []。

代码：
```solidity
{}
```"#, sliced_code);

        let response = self.call_llm(&prompt, 1024)?;
        
        // 日志：LLM原始响应
        println!("\n   [DEBUG] LLM阶段1原始响应:");
        println!("   {}", "─".repeat(50));
        for line in response.lines().take(20) {
            println!("   {}", line);
        }
        if response.lines().count() > 20 {
            println!("   ... (共 {} 行)", response.lines().count());
        }
        println!("   {}", "─".repeat(50));
        
        self.parse_missing_functions(&response)
    }

    /// 阶段2: AST从源码提取缺失函数
    pub fn complete_functional_code(&self, code: &str, missing_funcs: &[MissingFunction]) -> Result<String, String> {
        println!("\n� 阶段2: AST从源码提取缺失函数...");
        
        if missing_funcs.is_empty() {
            println!("   ℹ️  无需补全功能性函数");
            return Ok(code.to_string());
        }

        // 读取原始源码
        let source_code = if let Some(ref path) = self.source_file_path {
            std::fs::read_to_string(path)
                .map_err(|e| format!("读取源码文件失败 {}: {}", path, e))?
        } else {
            println!("   ⚠️  未设置源码文件路径，回退到LLM生成模式");
            return self.complete_functional_code_with_llm(code, missing_funcs);
        };

        println!("   [源码] 文件: {:?}, 大小: {} 字节", self.source_file_path, source_code.len());

        let mut completed_code = code.to_string();
        let mut extracted_count = 0;

        // 为每个缺失函数从源码提取
        for func in missing_funcs {
            println!("\n   [提取] {}.{} (优先级: {})", func.contract, func.name, func.priority);
            
            match self.extract_function_from_source(&source_code, &func.contract, &func.name) {
                Ok(func_code) => {
                    println!("   ✓ 成功提取，{} 字符, {} 行", func_code.len(), func_code.lines().count());
                    
                    // 插入到代码中（智能插入到对应的合约内部）
                    if let Some(inserted) = self.insert_function_into_contract(&completed_code, &func.contract, &func_code) {
                        completed_code = inserted;
                        extracted_count += 1;
                    } else {
                        println!("   ⚠️  无法插入到合约 {}，追加到末尾", func.contract);
                        completed_code.push_str("\n\n");
                        completed_code.push_str(&func_code);
                        extracted_count += 1;
                    }
                }
                Err(e) => {
                    println!("   ✗ 提取失败: {}", e);
                }
            }
        }
        
        println!("\n   [总结] 成功提取 {}/{} 个函数", extracted_count, missing_funcs.len());
        
        if extracted_count == 0 {
            println!("   ⚠️  未能从源码提取任何函数，回退到LLM生成模式");
            return self.complete_functional_code_with_llm(code, missing_funcs);
        }
        
        Ok(completed_code)
    }

    /// 阶段2备选: LLM补全功能性函数（简化实现）
    fn complete_functional_code_with_llm(&self, code: &str, missing_funcs: &[MissingFunction]) -> Result<String, String> {
        println!("\n   [LLM模式] 使用LLM生成缺失函数...");
        
        let func_list: Vec<String> = missing_funcs.iter()
            .map(|f| format!("- {}.{}()", f.contract, f.name))
            .collect();

        let prompt = format!(r#"你是Solidity代码专家。为以下函数或其所在的合约/依赖项提供**简化的功能实现**：

{}

**实现策略**：
- 核心函数（priority=1）：提供基本逻辑框架
- 次要函数（priority=2-3）：简单stub实现即可
- 如果缺失的是整个合约依赖（如 ERC20Minimal），请提供该合约的简化版本

**重要**：
1. **只返回新增的代码部分**（函数定义、库或合约桩）。
2. **绝对不要**包含原始代码，也不要返回完整的修复代码。
3. 请将所有新增代码放在一个 ```solidity 代码块中。

原始代码片段（仅供上下文参考）：
```solidity
{}
```"#, func_list.join("\n"), if code.len() > 2000 { &code[..2000] } else { code });

        let response = self.call_llm(&prompt, 4096)?;
        
        let new_code = self.extract_code_block(&response)?;
        
        println!("\n   [合并] 将生成的代码合并到原始代码中...");
        
        // 合并策略：将新生成的桩代码置于文件顶部，以确保依赖关系正确
        let mut final_code = String::new();
        final_code.push_str("// --- LLM Generated Stubs ---\n");
        final_code.push_str(&new_code);
        final_code.push_str("\n\n// --- Original Sliced Code ---\n");
        final_code.push_str(code);
        
        // 验证函数是否被补充（简单检查）
        println!("\n   [检查] 验证函数补充情况:");
        for func in missing_funcs {
            if final_code.contains(&func.name) {
                println!("   ✓ {} 已在生成的补丁中找到", func.name);
            } else {
                println!("   ✗ {} 未找到", func.name);
            }
        }
        
        Ok(final_code)
    }

    /// 阶段3: LLM最终修复使代码可编译 (已禁用)
    #[allow(dead_code)]
    pub fn final_compilation_fix(&self, code: &str) -> Result<String, String> {
        println!("\n� 阶段3: LLM最终编译修复 (已禁用)...");
        
        // 直接返回代码，不进行LLM修复
        println!("   ℹ️  阶段3已禁用，直接返回阶段2的结果");
        Ok(code.to_string())
    }

    /// 执行完整的三阶段补全流程
    pub fn run_completion_pipeline(&self, sliced_code: &str) -> Result<String, String> {
        println!("\n{}", "=".repeat(60));
        println!("🚀 启动三阶段LLM智能补全");
        println!("{}", "=".repeat(60));

        // 阶段1: 分析缺失函数
        let missing_funcs = self.analyze_missing_functions(sliced_code)?;
        
        if !missing_funcs.is_empty() {
            println!("   发现 {} 个关键缺失函数:", missing_funcs.len());
            for func in &missing_funcs {
                println!("   - {}.{} (优先级: {})", func.contract, func.name, func.priority);
            }
        }

        // 阶段2: 补全功能性代码
        let code_with_funcs = self.complete_functional_code(sliced_code, &missing_funcs)?;
        
        // 阶段3: 最终编译修复
        let final_code = self.final_compilation_fix(&code_with_funcs)?;
        
        println!("\n✅ 三阶段补全完成");
        println!("   原始代码: {} 行", sliced_code.lines().count());
        println!("   最终代码: {} 行", final_code.lines().count());
        
        Ok(final_code)
    }

    // === 私有辅助方法 ===

    fn call_llm(&self, prompt: &str, max_tokens: usize) -> Result<String, String> {
        use std::time::Duration;
        
        println!("   [LLM调用] 模型: {}, Max Tokens: {}, Prompt长度: {} 字符", 
                 self.model, max_tokens, prompt.len());
        
        let client = reqwest::blocking::Client::builder()
            .timeout(Duration::from_secs(180))
            .build()
            .map_err(|e| format!("创建HTTP客户端失败: {}", e))?;

        let request = LLMRequest {
            model: self.model.clone(),
            messages: vec![Message {
                role: "user".to_string(),
                content: prompt.to_string(),
            }],
            temperature: 0.1,
            max_tokens,
        };

        let response = client
            .post(format!("{}/chat/completions", self.base_url))
            .header("Authorization", format!("Bearer {}", self.api_key))
            .header("Content-Type", "application/json")
            .json(&request)
            .send()
            .map_err(|e| format!("API调用失败: {}", e))?;

        if !response.status().is_success() {
            return Err(format!("API错误: {}", response.status()));
        }

        let llm_response: LLMResponse = response
            .json()
            .map_err(|e| format!("解析响应失败: {}", e))?;

        let content = llm_response.choices[0].message.content.clone();
        println!("   [LLM响应] 长度: {} 字符, {} 行", content.len(), content.lines().count());
        
        Ok(content)
    }

    fn parse_missing_functions(&self, response: &str) -> Result<Vec<MissingFunction>, String> {
        // 提取JSON部分
        let json_str = if let Some(start) = response.find('[') {
            if let Some(end) = response.rfind(']') {
                &response[start..=end]
            } else {
                response
            }
        } else {
            response
        };

        println!("   [解析] 提取到的JSON字符串: {}", json_str);

        // 解析JSON
        #[derive(Deserialize)]
        struct FuncJson {
            name: String,
            contract: String,
            priority: usize,
        }

        let funcs: Vec<FuncJson> = serde_json::from_str(json_str)
            .unwrap_or_else(|e| {
                println!("   [警告] JSON解析失败: {}", e);
                vec![]
            });

        println!("   [解析] 成功解析 {} 个函数", funcs.len());

        Ok(funcs.into_iter().map(|f| MissingFunction {
            name: f.name,
            contract: f.contract,
            priority: f.priority,
        }).collect())
    }

    /// 从源码中提取指定合约的指定函数 (使用Solar AST精确提取)
    fn extract_function_from_source(&self, source_code: &str, contract_name: &str, func_name: &str) -> Result<String, String> {
        println!("      [AST] 解析源码以提取 {}.{}", contract_name, func_name);
        
        // 使用Solar解析AST
        let sess = Session::builder()
            .with_buffer_emitter(solar_interface::ColorChoice::Never)
            .build();
        
        let result = sess.enter(|| -> solar_interface::Result<Option<String>> {
            let arena = solar_ast::Arena::new();
            
            // 将源码写入临时文件，因为Parser::from_file需要文件路径
            let temp_dir = std::env::temp_dir();
            let temp_file = temp_dir.join("temp_source.sol");
            if let Err(e) = std::fs::write(&temp_file, source_code) {
                eprintln!("      [错误] 无法写入临时文件: {}", e);
                return Ok(None);
            }
            
            let mut parser = solar_parse::Parser::from_file(&sess, &arena, &temp_file)?;
            let ast = parser.parse_file().map_err(|e| e.emit())?;
            
            // 遍历AST查找目标合约和函数
            for item in ast.items.iter() {
                if let ItemKind::Contract(contract) = &item.kind {
                    if contract.name.to_string() == contract_name {
                        println!("      [AST] 找到合约 {}", contract_name);
                        
                        // 查找目标函数
                        for body_item in contract.body.iter() {
                            if let ItemKind::Function(func) = &body_item.kind {
                                if let Some(name) = &func.header.name {
                                    if name.to_string() == func_name {
                                        // 找到目标函数！提取其源码
                                        println!("      [AST] 找到函数 {}", func_name);
                                        
                                        // 使用span提取源码
                                        let span = body_item.span;
                                        let start = span.lo().to_usize();
                                        let end = span.hi().to_usize();
                                        
                                        if start < source_code.len() && end <= source_code.len() {
                                            let func_code = &source_code[start..end];
                                            println!("      [AST] 成功提取函数, span: {}..{}, {} 字符", start, end, func_code.len());
                                            return Ok(Some(func_code.to_string()));
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            Ok(None)
        });
        
        match result {
            Ok(Some(code)) => Ok(code),
            Ok(None) => Err(format!("未找到 {}.{}", contract_name, func_name)),
            Err(_) => Err("AST解析失败".to_string()),
        }
    }
    
    /// 将函数插入到指定合约内部
    fn insert_function_into_contract(&self, code: &str, contract_name: &str, func_code: &str) -> Option<String> {
        let lines: Vec<&str> = code.lines().collect();
        let mut result = Vec::new();
        let mut in_contract = false;
        let mut inserted = false;
        let mut contract_brace_count = 0;
        
        for (_i, line) in lines.iter().enumerate() {
            result.push(line.to_string());
            
            // 检测合约开始
            if !in_contract && line.contains(&format!("contract {}", contract_name)) {
                in_contract = true;
                contract_brace_count = 0;
            }
            
            if in_contract {
                contract_brace_count += line.chars().filter(|&c| c == '{').count() as i32;
                contract_brace_count -= line.chars().filter(|&c| c == '}').count() as i32;
                
                // 在合约结束大括号前插入
                if !inserted && contract_brace_count == 0 && line.trim().starts_with('}') {
                    // 在结束大括号前插入函数
                    let last_idx = result.len() - 1;
                    result.insert(last_idx, func_code.to_string());
                    inserted = true;
                    in_contract = false;
                }
            }
        }
        
        if inserted {
            Some(result.join("\n"))
        } else {
            None
        }
    }

    fn extract_code_block(&self, response: &str) -> Result<String, String> {
        // 尝试提取 ```solidity 代码块
        if let Some(start) = response.find("```solidity") {
            let code_start = start + "```solidity".len();
            if let Some(end) = response[code_start..].find("```") {
                let code = response[code_start..code_start + end].trim().to_string();
                println!("   [提取] 成功提取 ```solidity 代码块, {} 字符, {} 行", 
                         code.len(), code.lines().count());
                return Ok(code);
            }
        }

        // 尝试提取普通 ``` 代码块
        if let Some(start) = response.find("```") {
            let code_start = start + "```".len();
            if let Some(end) = response[code_start..].find("```") {
                let code = response[code_start..code_start + end].trim().to_string();
                println!("   [提取] 成功提取普通 ``` 代码块, {} 字符, {} 行", 
                         code.len(), code.lines().count());
                return Ok(code);
            }
        }

        // 如果没有代码块标记，返回整个响应
        println!("   [警告] 未找到代码块标记，返回完整响应");
        Ok(response.trim().to_string())
    }
}
