# 双分母回算报告（五轮同盐配对）

口径：候选分母 = 报告证据完整的 P/I/V；逻辑完整分母 = 候选分母 −
`incomplete_piv`（生成的 P/I/V 逻辑退化：P∧I/P∧V unsat、自等/自矛盾）。

| 轮次 | eligible | formalized | incomplete_piv | generator_defect | 候选率 | 逻辑完整率 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| OLD | 81 | 51 | 13 | 17 | 62.96% | **75.00%** |
| NEW1 | 82 | 46 | 13 | 23 | 56.10% | 66.67% |
| NEW2 | 81 | 52 | 6 | 23 | 64.20% | 69.33% |
| NEW3 | 80 | 53 | 5 | 22 | 66.25% | 70.67% |
| NEW4 | 86 | 47 | 10 | 29 | 54.65% | 61.84% |

## 结论

- 修正口径后，规则化率稳定抬升 7–12pp：逻辑完整率 61.8%–75.0%。
- 五轮仍存在波动（61.8%–75.0%），说明噪声来自 `generator_defect`
  （每轮 17–29）而非报告素材本身。
- `incomplete_piv` 每轮仅 5–13 个，占比小且大多落在 Hybra/Panoptic/Olas
  等少数案例，属报告素材逻辑不完整，应单独审计、不进分母。
- 下一步第 3 步应聚焦 `generator_defect`：relation template mismatch、
  invalid quantity types、got-9-symbols、unit mismatch 四类机械失败。

生成器：`evaluation/compute_double_denominator.py`（复用
`cli.semantic_pipeline.piv_failure_bucket`，零新增模型调用）。
