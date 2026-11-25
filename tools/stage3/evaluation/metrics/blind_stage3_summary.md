# 盲测阶段三结果

可运行子集 **10** 案例；stage2 run **10**；stage3 完成 **10**；claim 级复现 **11/32**。

| 案例 | claims | 复现 | verdicts |
| --- | ---: | ---: | --- |
| Liquid_Ron_C7vLJT2ME8Z__1000 | 2 | 2 | violation_reproduced |
| Liquid_Ron_C7vLJT2ME8Z__1027 | 2 | 2 | violation_reproduced |
| Liquid_Ron_C7vLJT2ME8Z__1036 | 10 | 0 | binding_error, compile_error, effect_observed_invariant_holds, stage2_restatement_required |
| Liquid_Ron_C7vLJT2ME8Z__104 | 4 | 3 | stage2_restatement_required, violation_reproduced |
| Lambo.win_LVoZUeMUNkB__102 | 1 | 0 | stage2_restatement_required |
| Lambo.win_LVoZUeMUNkB__105 | 1 | 1 | violation_reproduced |
| Lambo.win_LVoZUeMUNkB__119 | 2 | 2 | violation_reproduced |
| Silo_Finance_yjrYyfyTzWc__453 | 7 | 0 | binding_error, reference_patch_required, stage2_restatement_required, violation_not_reproduced |
| Liquid_Ron_C7vLJT2ME8Z__1032 | 1 | 1 | violation_reproduced |
| Silo_Finance_yjrYyfyTzWc__446 | 2 | 0 | binding_error, stage2_restatement_required |

## verdict 分布

| verdict | 数 |
| --- | ---: |
| binding_error | 7 |
| compile_error | 1 |
| effect_observed_invariant_holds | 1 |
| reference_patch_required | 1 |
| stage2_restatement_required | 9 |
| violation_not_reproduced | 2 |
| violation_reproduced | 11 |

## 根因（按影响排序）

- **binding_error**：7 个 claim 的 I/V 绑定形状或类型与代码事实不匹配，在 forge 前被拒绝。
- **stage2_restatement_required**：9 个 claim 命中快照/层错配等语义硬门，必须回到阶段二重述 I，不得算 TN 或 FN。
- **violation_reproduced**：11 个 claim 完成 original=Success / patched=Failure 的定向差分，其中参考补丁路由命中 3 个。
- **compile_error**：1 个 claim 的补丁版工程编译失败，按规则不计为漏洞成立。
- **effect/not_reproduced**：effect_observed_invariant_holds 1，violation_not_reproduced 2，说明 I 未在 exploit 路径上被证伪或差分未产生见证。

## 结论

盲测主线已端到端跑通（compile_blocked 0）；当前剩余损失由绑定错误、阶段二快照不变式和少量编译问题决定，不再是 stage-1 harness 缺失。
