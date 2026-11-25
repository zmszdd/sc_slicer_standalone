# A+/hardened/top-3 64-case smoke

- protocol: `mainline/1.6.1`
- protocol sha256: `9d2da075235c814f081fe6323850602e35363b4c6e57916827adee8c2d35c622`
- reportable: **false**（resolved-only smoke；负样本集仍以 blind-invalid 为主）
- manifest: `tools/stage3/evaluation/frozen/aplus_ab_resolved_20261120.json`

## 变更

1. `revert_expected` 路线不再豁免独立 effect gate；只有差分、没有独立 V
   witness 的 reproduced 结果降级为 `effect_not_witnessed`。
2. `execution_gate.metric_eligibility.consistency` 只使用报告文本推导的 impact
   sufficiency；trusted judge label 仍只控制漏洞级 eligibility。

## 四指标对比

| 指标 | A+/top3（1.6.0） | A+/hardened/top3（1.6.1） |
| --- | ---: | ---: |
| accuracy | 0.4912 | 0.7297 |
| recall | 0.8182 | 0.8125 |
| precision_vuln | 1.0 | 1.0 |
| precision_consistency | 0.54 | 0.8667 |
| F1_vuln | 0.9 | 0.8966 |

| 混淆/覆盖 | A+/top3 | A+/hardened/top3 |
| --- | ---: | ---: |
| TP | 27 | 26 |
| FN | 6 | 6 |
| FP_vuln | 0 | 0 |
| FP_consistency | 23 | 4 |
| TN | 1 | 1 |
| resolved positive | 33 | 32 |
| resolved negative | 24 | 5 |
| unresolved/timeout | 7 | 27 |

一致性精确率提升主要来自把缺少独立 effect witness 的负样本从 FP 改为
unresolved，而不是把它们判成 TN。覆盖率损失是真实代价，不能只报 precision。

## 剩余 4 个 consistency FP

- `SukukFi...__adpHMPzg22m`
- `SukukFi...__XZCPF3B6TAA`
- `SukukFi...__SievkxWuwDB`
- `SukukFi...__NAzNyo5uX8H`

这些案例至少有一个 reproduced claim 的报告文本 impact 为 `unknown`，因此
不依赖 trusted label 的报告内 gate 无法再收紧；继续靠标签过滤会造成泄漏。
