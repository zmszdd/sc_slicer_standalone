# 阶段二准确率/召回率重测（当前代码，2026-11-04）

- 样本：goldset_v2_pos91 的 88 份真实正样本（同 selection.json）
- 参数：deepseek-flash / concurrency=2 / formal-retries=2 / continue-on-review /
  claim-verdict=signals / lean-formal-input / semantic-live-26
- 输出：/tmp/recall_rerun_88_final_1793789722（18 批，全部 EXIT 0）

## 召回率（提取覆盖）

| 指标 | 旧（Nov 3 缓存） | 新（当前代码） | 变化 |
| --- | ---: | ---: | ---: |
| impact 候选率（规则化/证据完整） | 207/264 = 78.4% | 218/260 = 83.85% | +5.4pp |
| 逻辑完整率（规则化/逻辑完整分母） | 207/239 = 86.6% | 218/244 = 89.34% | +2.7pp |
| 报告级 ≥1 formalized impact | 68/88 = 77.3% | 70/88 = 79.55% | +2.3pp |
| 完整 formalized 报告 | 45/88 = 51.1% | 55/88 = 62.5% | +11.4pp |
| zero_output | 20/88 = 22.7% | 18/88 = 20.5% | −2.2pp |

## 准确率（忠实度，单位 impact_intent_pair）

| 指标 | 旧 | 新 |
| --- | ---: | ---: |
| faithful 占比（已审计对中通过） | ~70%（旧口径） | 310/344 = 90.1% |
| unfaithful 占比 | — | 18/344 = 5.2% |
| needs_review | — | 16/344 = 4.7% |
| not_completed | — | 21 |

## 失败桶（新）

- incomplete_piv = 16（direct_relation_infeasible 类）
- generator_defect = 26（schema/template/quantity/fidelity）
- fidelity_failed = 18 / needs_review = 16 / not_completed = 21

## 诚实说明

- 本轮为单次重跑（n=1），DeepSeek 服务端噪声仍存在；严格结论需 ≥3 轮复测。
- 提升主要来自 ingest.py P2.0 回退（无显式 Impact 区的报告从 Summary/Description 恢复 impact 证据）。
- 阶段三改动（P1.8c/P1.9）不影响阶段二指标。
