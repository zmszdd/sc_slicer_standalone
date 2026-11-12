# 阶段三工程结构

```text
tools/stage3/
├── cli/                     入口层（python -m cli.<script>）
│   ├── stage3_pipeline.py   单案例端到端编排
│   ├── stage3_eval_run.py   全自动评测（组装 + 多轮绑定 + 差分）
│   ├── stage3_autorun.py    一站式编排（eval -> 裁决闭环 -> 验收门）
│   ├── stage3_verdict_loop.py 裁决闭环（可修复裁决 -> 重提绑定 -> 重跑）
│   ├── stage3_acceptance.py 验收门（复现率 / 终态率 gating）
│   ├── stage3_assemble.py   阶段一/二产物组装案例（三阶段通道）
│   └── stage3_batch.py      批量运行案例并汇总
├── lib/                     共享库层
│   ├── spec_loader.py       载入并校验阶段二 run
│   ├── binding.py           binding.json 校验 + feedback 构造
│   ├── binding_validate.py  源感知 lint（含合约作用域校验）
│   ├── compile_retry.py     编译失败黑名单重试
│   ├── verdict_loop.py      裁决分类 + 修复提示
│   ├── codegen.py           P/I/V AST → Solidity 表达式
│   ├── patch.py             参考补丁 / AST 自动注入（多文件/多函数/合约作用域）
│   ├── case_builder.py      阶段一/二 → 阶段三案例组装与校验
│   ├── forge_runner.py      forge --json 运行与解析
│   ├── differential.py      测试差异 → code_query_results
│   └── verdict.py           调阶段二 ingest_feedback
├── codegen/templates/       补丁模板（M4 预留）
├── cases/                   案例：src/test/binding.json/stage2_run/expected
├── runs/                    运行产物（original/patched + 判定）
├── docs/                    工作流与绑定规范
└── tests/                   阶段三本地回归
```

分层规则与阶段二一致：`lib/` 不 import `cli/`；入口只做分发；运行用
`python -m cli.stage3_pipeline` 且 cwd 为 `tools/stage3/`。

计划但尚未实现：`lib/solbind.py`（Solidity AST 辅助绑定，留给更复杂的真实案例）。
