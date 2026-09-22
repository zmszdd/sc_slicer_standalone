# 报告驱动约束：三样例本地验证

后续已批准并运行 Brix 一次真实模型验证，发现 I/V 安全方向反转，详见 [AUTO_REPORT.md](AUTO_REPORT.md)。下文保留本地三候选验证的历史范围和结果。

最新完善方案、代码入口与验收状态见 [SECOND_STAGE_DESIGN.md](SECOND_STAGE_DESIGN.md) 和 [README.md](../README.md)，当前新增核心要素与形式化两层表示，不依赖切片成功。

后续新两步路径已真实复验，第一步因生成引文非原文连续片段而拒绝，第二步未运行；见 [TWO_STEP_REPORT.md](TWO_STEP_REPORT.md)。

日期：2026-09-12。目的：验证不同报告语义能否形成有证据、有边界的安全性质，再转成第三阶段可读取的规范。没有运行第一阶段、InvCon/Trace2Inv 或外部模型服务。

## 样例与结果

所有样例来自 `verified_flatten_pass_1568_exact_cases`，标识、报告来源身份和合约 SHA 均通过本地校验。候选全部由当前助手阅读描述与影响后推导，统一标记 `assistant_review`；不是外部模型批量自动抽取评测。

| 样例 | 报告推导的候选安全性质 | 已形式化的声称效果 | 必须保留的限制 |
|---|---|---|---|
| Brix 缓冲手续费 | 足额/超额支付不应单独造成手续费不匹配回退 | 费用不匹配回退且消息未发出 | 不保证其他原因下交易成功，不证明退款 |
| Ekubo 缺少 deadline | 超过用户指定时间的流动性操作不应完成 | 超时交易仍完成 | 用户 deadline 是规格意图，不是现存 Solidity 参数；经济损失未形式化 |
| GTE 权限报告 | 非指定 distributor 不应无授权地停用奖励累积 | null，保留未完成状态 | 原文检查描述与“反转”结论有疑点，且作者仅声称潜在影响并限定可利用性 |

三例的 I 都通过语法、类型/单位、引文、非空前提与 SMT 可解析性检查，状态为 `formalized_candidate`。这只意味着得到待审查的形式化候选。GTE 缺少确定 V 仍不阻止 I 的独立形式化，不能因此判断该报告可靠。

Ekubo 的 V 只覆盖时间效果，**不覆盖报告全部经济影响**；`missing_properties=[]` 只代表三个表达式槽非空，不代表完整语义覆盖。代码绑定、实际执行及语义准确率均未验证。第三阶段仍需复核范围，并建立 T。

## 已做的工具改进

1. 修正三反引号行内标记的过滤：如行首 ` ```withdraw()``` ` 不再被误判为多行代码块。匹配代码块关闭标记的字符与长度，避免意外保留或丢失正文。
2. 允许全部性质无法表达时以空符号、null 性质明确弃权，不虚构公式。
3. 外部提取必须显式使用 `--allow-report-upload`，还需用户授权；默认批处理为离线回放。
4. 添加小批处理入口 `run_report_batch.py` 和 `report_cases.json`。最多三份/三次调用、不重试、不覆盖既有结果；提取模式不读取助手候选。
5. 扩充保存结果复验、篡改拒绝及未授权调用不触发模型的测试。

## 文件与复验

最终本批结果：`results/report_only/batch_assistant_01/`，索引为 `batch-summary.json`；每例有原报告快照、推导输入、候选来源、约束、SMT、第三阶段待绑定规范及哈希。

```bash
/root/.local/share/uv/tools/halmos/bin/python tools/report_constraints_v2/verify_report_only.py \
  tools/report_constraints_v2/results/report_only/batch_assistant_01/brix_fee
/root/.local/share/uv/tools/halmos/bin/python tools/report_constraints_v2/verify_report_only.py \
  tools/report_constraints_v2/results/report_only/batch_assistant_01/ekubo_deadline
/root/.local/share/uv/tools/halmos/bin/python tools/report_constraints_v2/verify_report_only.py \
  tools/report_constraints_v2/results/report_only/batch_assistant_01/gte_access
```

重新生成本地批次（输出目录必须不存在）：

```bash
/root/.local/share/uv/tools/halmos/bin/python tools/report_constraints_v2/run_report_batch.py \
  --output runs/report_constraints_report_only/NEW_BATCH
```

本轮 40/40 回归测试通过，三例离线复验通过；保护检查确认 74 个文件未变。测试数不等于报告评测数，三例通过不能换算自动抽取准确率。第一阶段、Solar、原缓存及冻结 v1/ZIP 没有修改。

## 仍需完成

已单独询问是否授权发送所选报告描述与影响至配置的 `opencode-go/deepseek-v4-flash` 服务，最多三次调用。在获得明确回复前没有继续外发。获得授权后可运行：

```bash
/root/.local/share/uv/tools/halmos/bin/python tools/report_constraints_v2/run_report_batch.py \
  --mode extract --allow-report-upload --output runs/report_constraints_report_only/NEW_MODEL_BATCH
```

这一步应检验模型能否在未见本地助手候选公式的情况下自行提出合理性质，记录失败、语义覆盖、假设和服务报告用量。之后才选择一例做可选代码绑定与真正的第三阶段验证；现有接口始终 `execution_ready=false`、`consistency_verdict=not_evaluated`。
