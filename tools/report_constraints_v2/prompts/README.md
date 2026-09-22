# Prompt 目录说明

阶段二 Prompt 统一从 `registry.py` 注册。主流程不再逐个导入所有历史版本。

## 目录职责

| 路径 | 作用 | 修改规则 |
| --- | --- | --- |
| `definitions.py` | P/I/V 的集中式规范定义 | 修改语义定义时先改这里并评测 |
| `active.py` | 显式解析生产运行实际使用的两段 Prompt，并提供哈希 | 主流程只通过这里取得 Prompt |
| `registry.py` | 版本注册、默认版本和功能矩阵 | 新增版本时更新一次 |
| `versions/` | 冻结的历史 Prompt 实现 | 不原地改旧版本 |
| `versions/__init__.py` | 保持历史绝对导入可用 | 仅兼容，不放 Prompt 内容 |

`versions/` 中仍可看到 `import semantic_prompts_v...` 形式的内部导入。这是为了保留
历史 Prompt 的原始字节和哈希，由 `versions/__init__.py` 提供兼容，不是未迁移的
旧路径。新代码不得继续使用这种导入。

## 查看当前实际 Prompt

不调用模型即可查看集中定义或最终解析文本：

```bash
python main.py preview-prompt --part definitions
python main.py preview-prompt --part element
python main.py preview-prompt --part formal
python main.py preview-prompt --version semantic-v3.17 --part formal
```

`element` 和 `formal` 输出的正文就是流水线实际发送的对应提示词；版本、字节数和
SHA-256 写到标准错误。`active.py` 当前保持 v3.16 文本完全不变，只把运行时解析入口
集中起来，因此旧实验仍可按原版本重放。

## 版本作用

| 文件 | 公共版本 | 主要作用 |
| --- | --- | --- |
| `semantic_prompts_v35.py` | `semantic-v3.5` | 模型给计划、程序合成公式 |
| `semantic_prompts_v36.py` | `semantic-v3.6` | 核心 plan smoke 改进 |
| `semantic_prompts_v37.py` | `semantic-v3.7` | 结构化 unresolved |
| `semantic_prompts_v38.py` | `semantic-v3.8` | 前提支持与整除关系 |
| `semantic_prompts_v39.py` | `semantic-v3.9` | P 证据/时序提示 |
| `semantic_prompts_v310.py` | `semantic-v3.10` | 数值保真 |
| `semantic_prompts_v311.py` | `semantic-v3.11` | 地址保真 |
| `semantic_prompts_v312.py` | `semantic-v3.12` | 轻量第二步与稳定性恢复 |
| `semantic_prompts_v313.py` | `semantic-v3.13` | 动作角色规范化 |
| `semantic_prompts_v314.py` | `semantic-v3.14` | 复合限定、数值和 I/V 极性 |
| `semantic_prompts_v315.py` | `semantic-v3.15` | 12 类安全关系与关系对齐 |
| `semantic_prompts_v316.py` | `semantic-v3.16` | 固定模板、派生定义、局部修复 |
| `semantic_prompts_v317.py` | `semantic-v3.17` | 专用模板、impact 限定和来源绑定 |

这里列出当前仍注册的 v3.5–v3.17；v3–v3.4 已退役，其源码归档位于
`archives/stage2_v3_removal_20260922/`。冻结文件是实验可重放的一部分。即使多个版本只有少量差异，也不能把旧文本直接折叠为一个
会随时间变化的 Prompt。这里合并的是**注册、能力判断和使用入口**，而不是破坏性合并
冻结内容。新版本应新增文件并在 `registry.py` 登记。
