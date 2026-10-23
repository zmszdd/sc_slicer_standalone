# semantic-live-18：semantic-live-16 同一批 10 份报告复测

## 设置

- 使用上一轮同一组 10 份精确提交报告和 `report-json-input/5`。
- DeepSeek Flash；不向模型提供参考答案。
- readiness、要素和规则请求各允许一次重试；并发 2；`lean_formal_input` 与 `signals` 设置保持一致。
- Panoptic Next 因无前提 `P=true` 的兼容修复，在独立单报告批次补跑；该补跑使用相同模型和其余重试设置。
- 对最终 10 份产物执行零模型调用离线重放。

## 汇总

| 指标 | semantic-live-17 | semantic-live-18 |
|---|---:|---:|
| 完整来源 P/I/V Impact 分母 | 28 | 28 |
| 完整规则化通过 | 5（17.9%） | 6（21.4%） |
| I 来源对 | 43 | 49 |
| 生成规则数 | 40 | 45 |
| 忠实度通过 / 失败 / 未完成 | 13 / 11 / 19 | 12 / 33 / 4 |
| 完整批次模型调用 | 181 | 147 |
| 零调用离线重放 | 10/10 | 10/10 |
| 报告级候选通过 | 0/10 | 0/10 |

## 逐报告结果

| 报告 | 完整 P/I/V Impact | 完整规则化通过 | I 来源对 | 生成规则 | 忠实度通过/失败/未完成 | 调用 |
|---|---:|---:|---:|---:|---:|---:|
| Ekubo_3FTodhsvBkM | 2 | 0 | 4 | 4 | 1/3/0 | 13 |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC | 4 | 1 | 4 | 4 | 1/3/0 | 12 |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn | 3 | 0 | 4 | 3 | 1/2/1 | 14 |
| Hybra_Finance_xo4hapwL2Jy | 3 | 2 | 4 | 3 | 3/0/1 | 12 |
| Intuition_2VUsxVJwReb | 2 | 0 | 4 | 4 | 1/3/0 | 12 |
| Merkl_T4ExvutBBXC | 1 | 0 | 2 | 2 | 1/1/0 | 8 |
| Monetrix_L3gNZDymiju | 4 | 0 | 12 | 12 | 0/12/0 | 29 |
| Olas_j3PRAMM3fVq | 0 | 0 | 0 | 0 | 0/0/0 | 3 |
| Panoptic_Hypovault_c9MhophgwGP | 5 | 0 | 10 | 8 | 0/8/2 | 29 |
| Panoptic | 4 | 3 | 5 | 5 | 4/1/0 | 15 |

## 结果解读

- 完整规则化为 **6/28（21.4%）**；比 live-17 同批的 5/28（17.9%）多 1 项。
- 规则生成从 40 条增至 45 条；schema/validation 失败降为 2 项，公式构造失败 2 项。忠实度审查覆盖明显更多生成规则，但失败数也增至 33，说明瓶颈已经转到 P/I/V 关系忠实度。
- 10/10 份最终产物通过零调用重放（0 模型调用）；报告级候选通过仍为 0/10。
- 这批使用相同报告与设置，但模型输出有随机性，且各轮选出的 P/I 来源对不同；通过率变化不能单独归因于代码改动。忠实度由生成模型家族相同的审查模型给出，不是独立人工金标准。

逐条状态及复放数据见 `runs_01/`、`runs_02/`、`rerun_panoptic_next/`、`OFFLINE_REPLAY.json` 和 `RUN_SUMMARY.json`。
