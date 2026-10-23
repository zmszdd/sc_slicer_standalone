# semantic-live-17 多 I 来源独立规则化盲测

## 设置

- 10 份报告从冻结精确提交集确定性抽取，按 case ID、报告 SHA-256 和规范化输入 SHA-256 排除历史样本；抽样前没有按报告语义筛选。选择规则和输入哈希见 [`SELECTION.json`](SELECTION.json)，模型输入不含选择文件或参考答案。
- 使用 `semantic-live-17`、`report-json-input/5`、DeepSeek Flash。两个五例批次并发 2；readiness、要素和规则生成各允许一次重试，使用精简形式化输入和 `continue-on-review`。
- 每个选中的 `(Impact, I 来源)` 独立生成规则；统计分母按 Impact 计数，且某 Impact 的所有选中 I 规则都通过后，该 Impact 才计入规则化成功。
- 真实模型调用共 **159 次**。模型运行完成后，发现零调用 verifier 未覆盖 readiness 门提前停止的报告；只修复 verifier 并运行回归，随后 10/10 份产物零模型调用重放通过。修复时间和代码哈希变化记录在 [`POST_RUN_REPLAY_FIX.json`](POST_RUN_REPLAY_FIX.json)。

## 结果

| 指标 | 结果 |
|---|---:|
| 冻结报告 | 10 |
| 有完整报告依据的 P/I/V Impact 分母 | 28 |
| 所有已选 I 规则均完成的 Impact | 9/28（32.1%） |
| 独立 `(Impact, I)` 来源对 | 43 |
| 生成过规则的来源对 | 36/43 |
| 忠实度通过 / 失败 / 未完成 | 13 / 4 / 26 |
| 至少一个 Impact 完整规则化的报告 | 3/7 个有分母报告 |
| `candidate_checks_passed` 报告 | 1/10 |
| 实际模型调用 | 159 |
| 零调用 verify | 10/10 通过 |
| 全量本地回归 | 463/463 通过 |

| 报告 | 完整 P/I/V Impact | 通过 | I 来源对 | 规则生成 | 模型调用 |
|---|---:|---:|---:|---:|---:|
| Ekubo | 0 | — | 0 | 0 | 2 |
| GTE Perps and Launchpad | 4 | 0 | 4 | 0 | 12 |
| GTE Spot CLOB and Router | 0 | — | 0 | 0 | 2 |
| Hybra Finance | 2 | 0 | 6 | 6 | 22 |
| Intuition | 3 | 1 | 3 | 2 | 12 |
| Merkl | 0 | — | 0 | 0 | 1 |
| Monetrix | 5 | 5 | 6 | 6 | 18 |
| Olas | 1 | 0 | 3 | 3 | 16 |
| Panoptic Hypovault | 8 | 3 | 10 | 10 | 35 |
| Panoptic Next Core | 5 | 0 | 11 | 9 | 39 |

Ekubo 和 GTE Spot 没有明确标注的 Impact 区域；Merkl 在提取前筛选处停止。三者不进入规则化分母。其余 7 份报告提供 28 个完整来源 Impact，43 个独立 I 来源对，说明一个 Impact 关联多个 I 的情况确实出现。

assessment 中记录的失败阶段计数为 schema/validation 19、公式构造 4、语义忠实度 4、证据/覆盖 3。主要未解决瓶颈已从 live-16 的单 I schema 限制转为规则 schema/校验和来源覆盖；独立分对后规则生成量提高，但只有 9/28 个 Impact 的全部 I 规则完成。

## 对比边界

上一轮 semantic-live-16 在另一组 10 份报告上为 3/24（12.5%），其中 9 项因单 I schema 被跳过。live-17 本轮为 9/28（32.1%），且覆盖了 43 个独立 I 来源对。两轮样本不同，且本轮只 1/10 报告通过总候选门，因此这不是配对实验，也不能单凭通过率断言语义质量已提升。忠实度审查与规则生成使用同一模型家族，指标仍需人工抽样复核；Z3 与候选门通过也不代表 PoC/代码一致。

逐项结果、调用记录和重放证据保存在本目录的 `runs_01/`、`runs_02/`、[`OFFLINE_REPLAY.json`](OFFLINE_REPLAY.json) 及 [`RUN_SUMMARY.json`](RUN_SUMMARY.json)。
