# 阶段二真实报告金标准 v1

本目录包含五份公开、非敏感、相对清晰的真实漏洞报告，只保留 `title` 和描述/影响；不包含
PoC、修复建议或合约代码。

当前状态是 `assistant_draft_pending_human_review`，因此**尚不能用于宣称可信准确率**。
本目录的 25 项审核只用于批准这批参考样本，**不是阶段二处理新报告的运行门槛**。
通用批量处理采用[自动分流与抽样评测口径](../GENERALIZATION_PROTOCOL.md)。

## 文件

- `inputs/`：自包含的报告输入快照。
- `manifest.json`：公开来源、原报告哈希和输入快照哈希。
- `gold.json`：P/I/V、逻辑骨架、模态、证据锚点和预期 unresolved 草案。
- `REVIEW.md`：25 项人工审核卡。
- `approve_gold.py`：全部审核通过后生成带哈希的批准记录。
- `ratings.template.json`：对固定模型输出逐项评分的模板。
- `evaluate.py`：仅接受人工批准金标准和绑定输出哈希的人工评分。
- `run_blind.py`：对五份冻结输入运行 v3.7；程序不读取或发送 `gold.json`。

## 使用流程

```text
审核 REVIEW.md 并修订 gold.json
  -> 25 项全部 [x]
  -> approve_gold.py --reviewer NAME
  -> 固定 Prompt 对五份 inputs 盲测
  -> 复制并填写 ratings.template.json
  -> 人工确认 ratings，绑定 status/elements/formal-plan 哈希
  -> evaluate.py 输出受限范围准确率
```

盲测命令（输入均在 manifest 中明确标为公开、非敏感）：

```bash
python3 tools/report_constraints_v2/evaluation/gold_v1/run_blind.py \
  --allow-report-upload --output tools/report_constraints_v2/results/semantic/gold_v1_v37_01
```

准确率只表示这五份选择性、清晰报告上的表现，不代表所有漏洞报告的总体准确率。

首次 v3.7 盲测已经完成，结果见 [BLIND_REPORT.md](BLIND_REPORT.md)。工程链完成 2/5；
助手初评保存在 `ratings.assistant-preliminary.json`，但在人工批准前不会被评分程序接受。
