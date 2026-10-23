# semantic-live：完整 P/I/V 分母盲测

## 运行设置

- 从冻结的 1,568 份精确提交报告集中抽取 10 份此前未用过的报告；选择时排除了历史 case ID、原报告哈希和 report-input 哈希。抽样按项目分散，盐值、哈希和清单见 [`SELECTION.json`](SELECTION.json)。
- 测试版本：当前 `semantic-live`、`report-json-input/5`、DeepSeek Flash；模型未收到参考答案。
- 每个 manifest 最多 5 份；每批并发 2。要素和公式阶段各允许一次重试，失败案例继续运行到 review 状态。
- 10 份结果随后用仓库根 `main.py verify` 零模型调用重放。

## 统计口径与结果

分母只包含适用性判定选出的、P/I/V 都有报告依据的影响项。没有完整来源的项不进入分子、分母或汇总计数。完整来源项若公式生成失败，仍留在分母。某份报告分母为零时记为“不适用”，不按 0% 汇入总率。

| 报告 | 完整 P/I/V 分母 | 规则化通过 | 通过率 | 报告候选门 | 模型调用 |
|---|---:|---:|---:|---|---:|
| Ekubo | 3 | 1 | 33.3% | `candidate_checks_passed` | 15 |
| GTE Perps and Launchpad | 7 | 1 | 14.3% | `candidate_checks_passed` | 20 |
| GTE Spot CLOB and Router | 1 | 0 | 0% | `needs_review` | 7 |
| Hybra Finance | 7 | 1 | 14.3% | `candidate_checks_passed` | 25 |
| Intuition | 6 | 1 | 16.7% | `candidate_checks_passed` | 24 |
| Kinetiq | 不适用 | — | — | `needs_review` | 3 |
| Merkl | 1 | 0 | 0% | `needs_review` | 7 |
| Monetrix | 4 | 2 | 50% | `candidate_checks_passed` | 16 |
| Olas | 不适用 | — | — | `needs_review` | 3 |
| Panoptic Hypovault | 2 | 1 | 50% | `candidate_checks_passed` | 9 |
| **合计** | **31** | **7** | **22.6%** | **6/10 份报告通过** | **129** |

总率为 7/31。Kinetiq 和 Olas 没有完整来源候选，不进入统计；另外 24 个完整来源候选没有形成通过规则，按失败类型分为 schema/validation 16、证据或影响对齐 4、语义忠实度 4。`semantic_pipeline.py` 记录的分母和逐项适用性可以在每份运行产物的 `stage2-assessment.json` 与 `impact-applicability.json` 中复核。

10/10 个运行目录通过零模型调用 `verify`。共 129 次模型调用。报告候选门只说明工程检查结果；盲测没有独立人工金标准，不能据此将 7/31 解读成语义准确率。`consistency_verdict` 仍为 `not_evaluated`，也没有评估 PoC 与规格的一致性。

## 与上一批的比较边界

上一批 `prompt_live28_report_scope_blind_10` 为 6/25（24%）；本批为 7/31（22.6%）。样本不同，因此不能据此判断真实提升或退步。本批的主要价值是验证新分母落盘、重放和“不适用”处理在真实报告流水线中生效；它没有改变提示词，公式生成失败仍集中在 validation、来源对齐与语义忠实度。
