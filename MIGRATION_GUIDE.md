# SC_Slicer 迁移指南

## 概述

本文档说明如何将 SC_Slicer 从 Solar 项目中迁移出来，作为一个独立的工具。

## 迁移步骤

### 1. 创建独立项目结构

```bash
mkdir sc_slicer_standalone
cd sc_slicer_standalone
```

### 2. 创建 Cargo.toml

创建独立的 `Cargo.toml` 文件，只包含 SC_Slicer 所需的依赖：

```toml
[package]
name = "sc_slicer"
version = "0.1.0"
edition = "2021"
description = "Solidity code slicing analysis tool based on Program Dependency Graph (PDG)"
authors = ["Your Name <your.email@example.com>"]
license = "MIT OR Apache-2.0"
repository = "https://github.com/yourusername/sc_slicer"
keywords = ["solidity", "code-analysis", "pdg", "slicing", "security"]
categories = ["command-line-utilities", "development-tools"]

[dependencies]
# Solar crates for Solidity AST parsing and analysis
solar-ast = { path = "../solar/crates/ast" }
solar-interface = { path = "../solar/crates/interface" }
solar-parse = { path = "../solar/crates/parse" }
# Graph algorithms for PDG construction
petgraph = "0.6"
# Standard libraries
anyhow = "1.0"
clap = { version = "4.0", features = ["derive"] }
```

### 3. 复制核心文件

从 Solar 项目中复制必要的文件：

```bash
# 复制分析逻辑
cp ../solar/examples/src/analyzer.rs src/

# 复制示例合约（可选）
mkdir -p examples/src
cp ../solar/examples/src/Counter.sol examples/src/
```

### 4. 修改主程序

创建 `src/main.rs`，使用 clap 提供更好的命令行接口：

```rust
mod analyzer;

use clap::{Arg, Command};
use std::fs;
use std::process;

fn main() {
    let matches = Command::new("SC_Slicer")
        .version("0.1.0")
        .author("SC_Slicer Team")
        .about("Solidity code slicing analysis tool based on Program Dependency Graph (PDG)")
        .arg(
            Arg::new("contract_file")
                .help("Path to the Solidity contract file")
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
        .get_matches();

    // 解析参数并执行分析...
}
```

### 5. 修复依赖引用

修改 `analyzer.rs` 中的导入语句：

```rust
// 修改前
use solar::{
    ast::{self, Expr, ExprKind, Item, ItemKind, SourceUnit, Span, Stmt, StmtKind},
    interface::{Session, diagnostics::EmittedDiagnostics, BytePos},
    parse::Parser,
};

// 修改后
use solar_ast::{self as ast, Expr, ExprKind, Item, ItemKind, SourceUnit, Span, Stmt, StmtKind};
use solar_interface::{Session, diagnostics::EmittedDiagnostics, BytePos};
use solar_parse::Parser;
```

### 6. 修复类型引用

将 `solar::interface::Result` 替换为 `solar_interface::Result`：

```rust
// 修改前
let result = sess.enter(|| -> solar::interface::Result<AnalysisResult> {

// 修改后
let result = sess.enter(|| -> solar_interface::Result<AnalysisResult> {
```

### 7. 构建和测试

```bash
cargo build --release
cargo run -- --help
cargo run -- examples/src/Counter.sol Vault totalAssets
```

## 迁移结果

### 包含的文件

- `Cargo.toml` - 项目配置和依赖
- `src/main.rs` - 主程序入口，使用 clap 命令行解析
- `src/analyzer.rs` - 核心分析逻辑
- `examples/src/Counter.sol` - 示例 Solidity 合约
- `README.md` - 使用文档

### 排除的内容

- Solar 项目的其他组件（编译器、测试、文档等）
- 不必要的依赖和配置文件
- 其他工具和示例

### 优势

1. **独立性**：不再依赖完整的 Solar 项目
2. **轻量化**：只包含必要的代码和依赖
3. **可移植性**：可以独立分发和部署
4. **更好的 CLI**：使用 clap 提供现代化的命令行接口
5. **清晰的依赖关系**：明确声明了所需的 Solar 组件

## 注意事项

1. **路径依赖**：当前版本使用相对路径引用 Solar crates。在分发时需要调整为适当的依赖方式。

2. **Solar 版本兼容性**：确保使用的 Solar 版本与分析器代码兼容。

3. **许可证**：根据需要调整许可证声明。

4. **文档**：更新 README 中的路径和使用说明。

## 替代方案

如果不想使用路径依赖，可以考虑：

1. **发布到 crates.io**：将 SC_Slicer 发布为独立的 crate
2. **Git 依赖**：使用 git 依赖引用 Solar 仓库
3. **Vendoring**：将必要的 Solar 代码复制到项目中

这种迁移方式保持了 SC_Slicer 的核心功能，同时使其成为一个干净、独立的工具。