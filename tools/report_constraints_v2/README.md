# 阶段二：漏洞报告 P/I/V 提取与规则化

本目录只负责第二阶段：从漏洞报告的标题、描述和影响中推导报告声称的安全性质，并转换为
可审计的 P/I/V 约束。它不执行 PoC、不读取阶段一切片，也不判断 PoC 与报告是否一致。

- `P`：漏洞触发动作之前成立的报告场景前提；
- `I`：报告声称在限定条件下应保持的最窄安全性质；
- `V`：报告声称实际发生、且直接使 `I` 为假的可观察违反见证。

权威定义位于 [`prompts/definitions.py`](prompts/definitions.py)，查看时无需沿历史 Prompt
继承链查找。

## 当前工作流

```text
report.json
  → 提取 title / description / impact
  → DeepSeek 信息充分性检查
  → DeepSeek 提取带证据 ID 的语义要素
  → DeepSeek 选择安全关系、变量和形式计划
  → 程序确定性合成 P/I/V AST
  → 来源、类型、单位、数值、地址和可观察性检查
  → SMT / Z3 内部一致性检查
  → constraints.json / status.json / stage3-spec.json
```

Z3 通过只表示生成公式内部关系成立，不表示自然语言解释一定正确，也不表示 PoC 与报告一致。
后者需要阶段三把代码执行关系 `T` 与本阶段输出绑定后判断。

## 统一入口

在仓库根目录运行：

当前已验证的解释器是 `/root/.local/share/uv/tools/halmos/bin/python`。系统
`/usr/bin/python` 没有 Z3；未激活等价虚拟环境时，请用该完整路径替换下列 `python`。

```bash
python main.py doctor
python main.py versions
python main.py status
python main.py test
```

单案例真实运行：

```bash
python main.py run \
  --case-dir /absolute/path/to/case \
  --extract \
  --allow-report-upload \
  --output tools/report_constraints_v2/results/semantic/new-run-id
```

`main.py run` 默认使用官方 DeepSeek `deepseek-flash`。真实运行会发送筛选后的标题、描述、
影响以及流程生成的结构化要素；不会发送合约代码。输出目录必须不存在，避免覆盖历史结果。

批量运行：

```bash
python main.py batch \
  --reports-root /absolute/path/to/report-cases \
  --allow-report-upload \
  --output tools/report_constraints_v2/evaluation/new-batch-id
```

离线复验已有候选：

```bash
python main.py verify /absolute/path/to/run-directory
```

日常流程只需要 `run`、`batch`、`verify` 和下面的预览命令。`audit-preconditions`、
`repair-preconditions`、`observability`、`salvage-replay` 是发生特定警告后的高级诊断工具，
不会自动插入默认流程。

## 本地预览

以下命令不调用模型：

```bash
python main.py screen --case-dir /absolute/path/to/case
python main.py preview-report --case-dir /absolute/path/to/case
python main.py preview-plan --case-dir /absolute/path/to/case --elements elements-ids.json

python main.py preview-prompt --part definitions
python main.py preview-prompt --part element
python main.py preview-prompt --part formal
```

`preview-prompt` 会输出流水线实际使用的最终 Prompt，并在标准错误中给出版本、字节数和
SHA-256，不读取 API Key。

## 输入

推荐输入是案例目录中的 `report.json`：

```text
case/
├── report.json      # 必需：标题、描述和影响
└── metadata.json    # 可选：仅核对报告/案例身份
```

当前 P/I/V 提取不会读取合约代码、PoC、修复 diff、阶段一切片结果、历史运行结果或参考答案。
提取前筛选检查受影响对象、触发动作、直接效果和安全关系依据。明确缺失关键信息时在
P/I/V 生成前停止；这只是输入充分性判断，不是漏洞真假判断。

## 主要输出

```text
provenance.json          输入、模型、Prompt 版本及最终 Prompt 哈希
input-readiness.json     提取前信息充分性结论
evidence-catalog.json    编号后的原文片段
elements-ids.json        实体、P、动作、根因、I、影响和证据 ID
formal-plan.json         关系类别、变量、P 谓词和逻辑计划
formalization.json       程序生成的 P/I/V AST
constraints.json         编译及校验后的约束 bundle
solver-results.json      SMT/Z3 查询结果
auto-triage.json         candidate / review / abstain 分流
stage3-spec.json         阶段三待绑定接口
status.json              本次运行状态
```

`stage3-spec.json` 当前始终标记 `execution_ready=false`、
`code_alignment_status=not_attempted` 和 `consistency_verdict=not_evaluated`。

## 目录职责

```text
report_constraints_v2/
├── cli/                     入口层（由 main.py 调用）
│   ├── semantic_pipeline.py 主流程
│   ├── batch_verify.py      批量运行 + 零模型离线复验
│   ├── preview.py           输入、计划和 Prompt 预览
│   └── preconditions.py     可选 P 审计与受约束修复
├── lib/                     共享库层
│   ├── semantic_core.py     schema、来源、类型与 bundle 校验
│   ├── plan_synthesizer.py  确定性 P/I/V 公式合成
│   ├── report_only.py       报告解析、表达式基础设施和 DeepSeek 传输
│   ├── ingest.py            证据编号与原文回填 + 提取前信息充分性门
│   ├── solving.py           SMT/Z3 查询 + 可观察性审查与自动分流
│   ├── salvage.py           数值与地址保真检查 + 显式启用的机械规范化
│   └── compat.py            历史模块名兼容注册（meta path finder）
├── prompts/                 当前定义、运行时解析和冻结 Prompt 版本
├── tests/                   自动回归
├── samples/                 固定测试样例
├── evaluation/              评测证据与冻结运行
├── results/                 本地运行产物
├── review_samples/          人工审核材料
└── docs/                    设计、状态、流程和历史记录
```

进一步说明见：

- [工程结构](STRUCTURE.md)
- [阶段二设计](docs/SECOND_STAGE_DESIGN.md)
- [当前状态](docs/STAGE2_CURRENT_STATUS.md)
- [完整文件级流程](docs/STAGE2_FLOW.md)
- [安全关系分类](docs/SAFETY_RELATION_TAXONOMY.md)

## Prompt 管理

- P/I/V 规范只在 `prompts/definitions.py` 维护；
- 主流程只通过 `prompts/active.py` 获取最终 Prompt；
- `prompts/registry.py` 管理版本、`feature_enabled`/`features_for` 功能开关；
- 唯一可编辑的 Prompt 是 `prompts/current.py`（`semantic-live`，默认版本），
  原地修改；每次 neural 运行把精确 prompt 快照与功能开关决策写进 run 目录，
  离线重放依据快照而非 current.py 当前内容；
- `prompts/versions/` 是冻结只读存档（v3.5–v3.20），供旧 run 回放，不再修改；
- 推荐稳定版仍标记为 `semantic-v3.16`（冻结）；政策细节见
  `docs/PROMPT_LIVE_POLICY.md`。

## 测试与归档

```bash
/root/.local/share/uv/tools/halmos/bin/python main.py test
python main.py frozen
```

早期 v1 已完整归档到 `archives/report_constraints_v1_20260912.zip`，活动目录
`tools/report_constraints/` 已删除。早期阶段二工具和事故记录位于
`archives/stage2_legacy_cleanup_20260922/`，不属于当前工作流。
