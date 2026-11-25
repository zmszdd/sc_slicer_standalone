# 历史 Stage-3 run 摘要证据包

本目录只保存文档和历史指标中引用过的 `stage3-summary.json`，用于解释旧实验、
失败模式和方案演进。它不是当前协议 run，也不进入权威四指标分母。

- 生成脚本：`scripts/collect_legacy_run_evidence.py`
- 索引与 SHA256：`manifest.json`
- 原始 run 目录：`tools/stage3/runs/`，本机保留，不进入版本控制

这些摘要可能来自 dev24、smoke、旧协议或候选实验；其中的路径和 verdict 只反映
当时的运行上下文。不要把它们当作 `mainline/1.7.36` 的结果，也不要据此修改标签、
放宽 gate 或重算权威指标。
