# SC_Slicer - 独立的 Solidity 代码切片分析工具

SC_Slicer 是一个独立的 Solidity 智能合约代码切片分析工具，基于程序依赖图 (PDG) 技术。该工具专门用于 Solidity 代码的安全审计和依赖分析，能够提取与特定变量相关的代码片段。

## 功能特性

- **跨合约分析**：能够分析多个合约之间的依赖关系
- **程序依赖图 (PDG)**：构建完整的程序依赖图，包含数据流和控制流依赖
- **智能代码切片**：提供两种切片模式
  - **函数级切片**：提取包含相关节点的完整函数代码
  - **行级切片**：提取具体的相关源代码行，提供更精确的分析
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

## 工作原理

SC_Slicer 通过以下步骤进行代码分析：

1. **AST 解析**：使用 Solar 编译器解析 Solidity 源代码
2. **依赖图构建**：构造程序依赖图 (PDG)，包含数据流和控制流依赖
3. **切片计算**：从指定的变量开始，向后追踪所有相关代码
4. **结果提取**：根据切片级别提取函数级或行级代码片段

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