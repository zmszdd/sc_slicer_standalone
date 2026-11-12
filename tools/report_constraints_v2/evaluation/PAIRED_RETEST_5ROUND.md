# 五轮同盐配对复测（live26-fix confirm30）

## 实验口径

- 同一 30 份报告（六批清单逐字节一致，跨五轮复用，true paired）。
- 同一 prompt `semantic-live-26`、同一参数：`deepseek-flash`、`temperature=0`、
  `thinking=disabled`、`--element-retries 1 --formal-retries 1 --concurrency 2`。
- OLD / NEW1 = `direct_relation` 修复前；NEW2 / NEW3 / NEW4 = 修复后。

## 汇总表

| 轮次 | 条件 | direct_relation_infeasible | 规则化率 | candidate_checks_passed | 模型调用 | fidelity_failed | fidelity_needs_review | fidelity_not_completed | schema_or_validation | formula_construction |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| OLD | 修复前 | 14 | 51/81（63.0%） | 11/30 | 425 | 12 | 4 | 11 | 8 | 3 |
| NEW1 | 修复前 | 14 | 46/82（56.1%） | 11/30 | 451 | 13 | 3 | 17 | 8 | 9 |
| NEW2 | 修复后 | 9 | 52/81（64.2%） | 14/30 | 448 | 19 | 5 | 6 | 4 | 2 |
| NEW3 | 修复后 | 7 | 53/80（66.2%） | 14/30 | 388 | 5 | 6 | 13 | 6 | 7 |
| NEW4 | 修复后 | 16 | 47/86（54.7%） | 11/30 | 478 | 7 | 6 | 27 | 17 | 10 |

## 逐指标解读

- `direct_relation_infeasible`：修复前 14、14；修复后 9、7、16。2/3 轮更低，
  但 NEW4=16 高于任一修复前轮，**无法拒绝“修复无效果”的原假设**，属采样噪声。
- 规则化率：63.0 / 56.1 / 64.2 / 66.2 / 54.7，五轮极差约 12 个百分点，
  NEW4 比两轮修复前都低，**无可靠趋势**。
- `candidate_checks_passed`：11 / 11 / 14 / 14 / 11，NEW4 回落，**无可靠趋势**。
- `fidelity_not_completed`：11 / 17 / 6 / 13 / 27，是最大噪声源（极差 21）。
- `rejected`：Phase A 之后五轮均为 0，inventory 崩溃降级修复有效且稳定。

## 结论（诚实版）

1. Phase A（inventory 崩溃降级）稳定有效：`rejected=0` 且不再顶层崩溃。
2. `direct_relation` 反符号修复的机制是真的（修的是 `x AND NOT x` 的具体形态），
   但它在指标级的效果被模型服务端非确定性完全淹没，**不能宣称有改善**。
3. 当前测量协议（每条件 1 轮、读单轮差值）不可解释；此前“14→9→7 好转”是噪声，
   NEW4 已用 16 证明这一点。
4. 在固定 `temperature=0` 下仍出现如此大波动，说明方差主要来自服务端/流水线，
   不是可调采样参数。

## 下一步（先修测量，再谈改代码）

1. 每条件 ≥3 轮，报 `median + IQR`，其余全部冻结，停止读单轮差值。
2. 压噪：formalization 瓶颈改 `deepseek-v4-pro`，或每案例 n=3 多数投票取共识。
3. 压噪后再看主瓶颈：NEW4 里 `schema_or_validation=17`、
   `formula_construction=10` 已超过 `direct_relation_infeasible=16`，
   更值得优先处理，且更偏机械、更少受模型噪声影响。
