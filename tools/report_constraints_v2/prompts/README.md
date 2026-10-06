# Prompt 目录说明

阶段二 Prompt 统一从 `registry.py` 注册。当前政策是**单一活文件**：只有
`current.py`（`semantic-live`）可以被原地修改，`versions/` 是只读冻结存档。
政策细节与重放契约见 `docs/PROMPT_LIVE_POLICY.md`。

## 目录职责

| 路径 | 作用 | 修改规则 |
| --- | --- | --- |
| `current.py` | 唯一活 Prompt（`semantic-live`），初始文本 = v3.20 平铺 | **原地修改**；功能开关在 `FEATURES` 同步改 |
| `definitions.py` | P/I/V 的集中式规范定义 | 修改语义定义时先改这里并评测 |
| `active.py` | 显式解析生产运行实际使用的两段 Prompt，并提供哈希 | 主流程只通过这里取得 Prompt |
| `registry.py` | 版本注册、默认版本、`feature_enabled`/`features_for` 功能矩阵 | 冻结集合不动；live 变更只影响 current |
| `versions/` | 冻结的历史 Prompt 实现（只读存档） | 不再修改、不再新增 |
| `versions/__init__.py` | 保持历史绝对导入可用 | 仅兼容，不放 Prompt 内容 |

`versions/` 中仍可看到 `import semantic_prompts_v...` 形式的内部导入。这是为了保留
历史 Prompt 的原始字节和哈希，由 `versions/__init__.py` 提供兼容，不是未迁移的
旧路径。新代码不得继续使用这种导入；新改动一律落在 `current.py`。

## 查看当前实际 Prompt

不调用模型即可查看集中定义或最终解析文本：

```bash
python main.py preview-prompt --part definitions
python main.py preview-prompt --part element
python main.py preview-prompt --part formal
python main.py preview-prompt --version semantic-v3.20 --part formal
```

`element` 和 `formal` 输出的正文就是流水线实际发送的对应提示词；版本、字节数和
SHA-256 写到标准错误。默认输出即 live 文本。每次 neural 运行还会把精确 prompt
文本快照到 run 目录（`prompt-element.txt` / `prompt-formal.txt`），离线重放
依据快照而非 `current.py` 的当前内容，因此原地修改 live 不破坏历史 run 的
可验证性。

## 版本作用（冻结存档）

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
| `semantic_prompts_v318.py` | `semantic-v3.18` | 收敛矛盾判定与 truth binding 边界 |
| `semantic_prompts_v319.py` | `semantic-v3.19` | access_control 内容/grounding 规则冲突修正 |
| `semantic_prompts_v320.py` | `semantic-v3.20` | sequence_domain_fork 两条配方（live 的生成基线） |

v3–v3.4 已退役，其源码归档位于 `archives/stage2_v3_removal_20260922/`。冻结文件
是实验可重放的一部分：历史 run 的 provenance 引用旧版本名，`registry.module_for`
继续解析它们，但冻结内容永不折叠、不修改。新的迭代只在 `current.py` 原地进行，
其正确性由运行目录快照 + `provenance.prompt_features` 的重放契约保证。
