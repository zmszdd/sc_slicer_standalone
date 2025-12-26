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
- **输出大小控制**：提供多种选项控制输出内容的详细程度
  - **排除库函数**：过滤掉冗余的库实现代码
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
- `-o, --output <FILE>`：将结果输出到指定文件
- `--exclude-libs`：排除库函数和合约，只保留接口和类型定义
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

3. **指定函数名**：
   ```bash
   cargo run -- examples/src/Counter.sol Vault totalAssets deposit
   ```

4. **输出到文件**：
   ```bash
   cargo run -- examples/src/Counter.sol Vault totalAssets --output slice_result.txt
   ```

5. **排除库函数（减少输出大小）**：
   ```bash
   cargo run -- ./examples/src poc_final availableForWithdrawal --exclude-libs -o ./result_filtered.txt
   ```
   *效果：输出从 37,075 行减少到 3,571 行（减少约90%）*

6. **最小化输出（排除库函数和类型定义）**：
   ```bash
   cargo run -- ./examples/src poc_final availableForWithdrawal --exclude-libs --include-types=false -o ./result_minimal.txt
   ```

7. **完整分析（包含所有依赖）**：
   ```bash
   cargo run -- ./examples/src poc_final availableForWithdrawal --level line -o ./result_complete.txt
   ```

## 工作原理

SC_Slicer 通过以下步骤进行代码分析：

1. **AST 解析**：使用 Solar 编译器解析 Solidity 源代码
2. **依赖图构建**：构造程序依赖图 (PDG)，包含数据流和控制流依赖
3. **切片计算**：从指定的变量开始，向后追踪所有相关代码
4. **输出过滤**：根据用户选项过滤不需要的库函数和类型定义
5. **结果提取**：根据切片级别提取函数级或行级代码片段

### 输出大小优化

工具提供了多种选项来控制输出大小：

- **默认模式**：包含所有相关代码，可能输出较大
- **排除库函数**：过滤掉 `library` 和 `contract` 的完整实现，只保留接口
- **类型定义控制**：可以选择不包含 `struct`、`enum` 等类型定义
- **组合使用**：可以同时使用多个过滤选项获得最小化输出

实际案例显示，使用 `--exclude-libs` 选项可以将输出从 37,075 行减少到 3,571 行。

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