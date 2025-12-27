# SC_Slicer - 独立的 Solidity 代码切片分析工具

SC_Slicer 是一个独立的 Solidity 智能合约代码切片分析工具，基于程序依赖图 (PDG) 技术。该工具专门用于 Solidity 代码的安全审计和依赖分析，能够提取与特定变量相关的代码片段。

## ⚠️ 输出大小说明

如果您的切片输出过大（例如超过数万行），请使用 `--exclude-libs` 选项来过滤库函数实现，这可以将输出大小减少约90%。详情请见下面的使用示例。

## 功能特性

- **跨合约分析**：能够分析多个合约之间的依赖关系
- **程序依赖图 (PDG)**：构建完整的程序依赖图，包含数据流和控制流依赖
- **智能代码切片**：提供两种切片模式
  - **函数级切片**：提取包含相关节点的完整函数代码
  - **行级切片**：提取具体的相关源代码行，提供更精确的分析
- **语义切片 (Semantic Slicing)**：基于LLM的智能相关性分析
  - **扩展相关性定义**：识别跨合约上游数据修改
  - **并发评分**：并行处理相关性分析，提高性能
  - **依赖链追踪**：严格按照修改→读取→计算的依赖链分析
- **递归依赖追踪**：自动追踪完整的函数调用链，包括库函数和底层实现
- **通用性分析**：基于 AST 分析动态识别相关合约/库，无需硬编码配置
- **输出大小控制**：提供多种选项控制输出内容的详细程度
  - **智能库筛选**：自动包含定义了相关函数的库，排除无关库代码
  - **类型定义控制**：选择是否包含结构体和类型定义
- **安全审计支持**：帮助识别潜在的安全漏洞和依赖问题
- **灵活输出**：支持控制台输出和文件输出两种模式

## 安装

### 环境要求
- Rust 1.88 或更高版本
- Cargo 包管理器

### 构建项目
```bash
git clone https://gitee.com/w1060/sc_slicer_standalone.git
cd sc_slicer_standalone
cargo build --release
```

## 使用方法

### 基本用法

```bash
cargo run -- <合约文件> <合约名> <变量名> [选项]
```

### 参数说明

- `<合约文件>`：要分析的 Solidity 合约文件路径
- `<合约名>`：合约的名称
- `<变量名>`：要进行切片分析的变量名称

### 选项

- `[函数名]`：可选参数，指定函数名称（如果变量在特定函数中）
- `-l, --level <LEVEL>`：切片级别
  - `function`：函数级切片（默认）
  - `line`：行级切片
- `--semantic`：启用语义切片，使用LLM进行智能相关性分析
- `--api-key <KEY>`：LLM API密钥（启用语义切片时必需）
- `-o, --output <FILE>`：将结果输出到指定文件
- `--exclude-libs`：智能排除无关库，只保留定义了相关函数的库实现
- `--include-types`：包含类型定义和结构体（默认启用）

### 示例

1. **函数级切片**（默认）：
   ```bash
   cargo run -- examples/src/Counter.sol Vault totalAssets
   ```

2. **行级切片**：
   ```bash
   cargo run -- examples/src/Counter.sol Vault totalAssets --level line
   ```

3. **语义切片**（推荐）：
   ```bash
   cargo run -- examples/src/Counter.sol Vault totalAssets --semantic
   ```
   *效果：使用LLM进行智能相关性分析，识别跨合约依赖关系*

4. **语义切片（带API密钥）**：
   ```bash
   cargo run -- examples/src/Counter.sol Vault totalAssets --semantic --api-key YOUR_API_KEY
   ```
   *效果：启用LLM API调用进行更准确的相关性分析*

5. **指定函数名**：
   ```bash
   cargo run -- examples/src/Counter.sol Vault totalAssets deposit
   ```

6. **输出到文件**：
   ```bash
   cargo run -- examples/src/Counter.sol Vault totalAssets --output slice_result.txt
   ```

7. **智能库筛选（推荐）**：
   ```bash
   cargo run -- ./examples/src/poc_final.t.sol PoC availableForWithdrawal --exclude-libs -o ./result_smart.txt
   ```
   *效果：自动包含关键库（如 PanopticMath、Math_2、TokenId），输出 27,077 行完整代码*

8. **语义切片 + 智能库筛选**：
   ```bash
   cargo run -- ./examples/src/poc_final.t.sol PoC availableForWithdrawal --semantic --exclude-libs -o ./result_semantic.txt
   ```
   *效果：结合LLM智能分析和库筛选，提供最准确的代码切片*

9. **传统库排除**：
   ```bash
   cargo run -- ./examples/src/poc_final.t.sol PoC availableForWithdrawal --exclude-libs --no-smart-filter -o ./result_filtered.txt
   ```
   *效果：传统模式，输出 3,977 行精简代码*

10. **最小化输出（排除库函数和类型定义）**：
    ```bash
    cargo run -- ./examples/src poc_final availableForWithdrawal --exclude-libs --include-types=false -o ./result_minimal.txt
    ```

11. **完整分析（包含所有依赖）**：
    ```bash
    cargo run -- ./examples/src poc_final availableForWithdrawal --level line -o ./result_complete.txt
    ```

## 工作原理

SC_Slicer 通过以下步骤进行代码分析：

1. **AST 解析**：使用 Solar 编译器解析 Solidity 源代码
2. **依赖图构建**：构造程序依赖图 (PDG)，包含数据流和控制流依赖
3. **切片策略选择**：
   - **传统切片**：基于静态分析的依赖追踪
   - **语义切片**：结合LLM的智能相关性分析，识别跨合约依赖关系
4. **递归依赖追踪**：从目标变量开始，向后追踪所有相关代码，包括完整的函数调用链
5. **智能合约识别**：基于 AST 分析自动识别定义了相关函数的合约和库
6. **输出过滤**：根据用户选项和依赖关系智能过滤不需要的代码
7. **结果提取**：根据切片级别提取函数级或行级代码片段

### 语义切片 (Semantic Slicing)

语义切片是SC_Slicer的最新功能，通过集成大语言模型(LLM)提供更智能的代码相关性分析：

- **扩展相关性定义**：不仅识别直接读写操作，还能识别跨合约的上游数据修改
- **依赖链追踪**：严格按照"修改→读取→计算目标变量"的依赖链进行分析
- **并发评分**：使用Rust异步并发技术并行处理多个函数的相关性分析
- **智能Prompt设计**：专门优化的LLM提示词，确保准确识别复杂依赖关系

**相关性评分标准**：
- 10分：直接写入目标变量
- 8-9分：修改关键变量（如价格），影响目标变量计算
- 5-7分：设置依赖关系（如设置合约地址）
- 1-4分：影响控制流逻辑
- 0分：完全无关

### 语义切片示例

语义切片能够识别复杂的跨合约依赖关系：

```solidity
// 合约A：设置价格
contract PriceSetter {
    uint256 public price;
    function setPrice(uint256 _price) external {
        price = _price;
    }
}

// 合约B：使用价格计算
contract Calculator {
    PriceSetter public priceContract;
    
    function calculate() external view returns (uint256) {
        uint256 currentPrice = priceContract.price();
        return currentPrice * 2;  // 目标变量依赖于price
    }
}
```

使用语义切片分析 `Calculator.calculate()` 中的 `currentPrice * 2`：

```bash
cargo run -- examples/cross_contract.sol Calculator "currentPrice * 2" --semantic --api-key YOUR_API_KEY
```

**输出结果**：
- `PriceSetter.setPrice()`：评分8分（修改关键变量）
- `PriceSetter.price()`：评分9分（直接读取目标依赖变量）
- `Calculator.constructor`：评分6分（设置依赖关系）
- 其他无关函数：评分0分（完全无关）

### 输出大小优化

工具提供了多种选项来控制输出大小：

- **默认模式**：包含所有相关代码，可能输出较大
- **智能库筛选**：自动包含相关库的完整实现，排除无关库代码
- **类型定义控制**：可以选择不包含 `struct`、`enum` 等类型定义
- **组合使用**：可以同时使用多个过滤选项获得最小化输出

实际案例显示，智能筛选可以将输出从 37,075 行优化到包含完整关键库的 27,077 行，同时保持代码的完整性和可分析性。

### 性能对比

| 模式 | 处理时间 | 输出行数 | 准确性 | 特点 |
|------|----------|----------|--------|------|
| 传统切片 | ~2秒 | 27,077行 | 中等 | 基于静态分析，快速但可能遗漏复杂依赖 |
| 语义切片 | ~15秒 | 智能筛选 | 高 | LLM分析，准确识别跨合约依赖关系 |

*注：语义切片时间主要消耗在LLM API调用上，但提供更准确的相关性分析*

## 示例合约

项目包含一个示例 Solidity 合约 `examples/src/Counter.sol`，您可以使用它来测试工具功能。

## 依赖项

- `solar`：Solar AST 库，用于 Solidity 解析
- `petgraph`：图算法库，用于 PDG 构造
- `clap`：命令行参数解析
- `anyhow`：错误处理

## 许可证

本项目采用 MIT 或 Apache-2.0 双许可证。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个工具。

cd /root/RCLI/sc_slicer_standalone && rm -f analysis.log && cargo run -- /root/RCLI/sc_slicer_standalone/examples/src/poc_final.t.sol PoC availableForWithdrawal --semantic