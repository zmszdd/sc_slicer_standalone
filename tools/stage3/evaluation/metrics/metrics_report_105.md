# 主线客观指标报告（案例级 + 项目级）

> 口径：四指标以判例锚定混淆矩阵为准（TP/FN 来自判例 valid/fixed/
> wontfix 相关样本，FP/TN 来自判例 invalid 独立负样本）。
> 构造负样本 100% 仅为内部一致性自检，不作为对外准确率/F1。

## 1. 主线漏斗（案例级）

| 阶段 | 数量 | 通过率 |
| --- | ---: | ---: |
| 阶段一 flatten | 105 | 100.0% |
| 阶段二 spec 非空 | 103 | 98.1% |
| 阶段三 动态终态 | 75 | 71.4% |
| 阶段三 复现(机械) | 69 | 65.7% |
| 阶段三 动态未复现 | 6 | 5.7% |

## 2. 覆盖损失（未到动态终态的案例，按原因）

| 原因 | 案例数 |
| --- | ---: |
| stage3:mixed_non_dynamic | 14 |
| stage3:partial_binding | 7 |
| stage3:inconclusive | 3 |
| stage3:not_dynamically_expressible | 2 |
| stage3:reference_patch_required | 1 |
| stage2:no_bound_claims | 1 |
| stage2:no_stage2_run | 1 |
| stage2:stage2_blocked | 1 |
| **合计** | **30** |

### 2.1 覆盖损失（claim 级，非动态 claim 按根因摊开）

| 原因 | claim 数 |
| --- | ---: |
| stage3:partial_binding | 69 |
| stage3:reference_patch_required | 39 |
| stage3:compile_error | 27 |
| stage3:inconclusive | 24 |
| stage3:not_dynamically_expressible | 15 |
| stage3:binding_failed | 6 |
| stage3:poc_not_witnessed | 3 |
| stage3:invariant_holds_on_exploit_path | 2 |
| stage3: | 1 |
| stage3:binding_error | 1 |
| **合计** | **187** |

### 2.2 多 claim 状态混杂明细（案例级桶与 claim 级根因并列）

| case | 案例级桶 | claim 级拆分 |
| --- | --- | --- |
| Brix_Money_qy7NXr77sDh__PGwVR6CTD6U__3hfE23tsgzG | dynamic | compile_error:3; partial_binding:8 |
| Forte__Float128_Solidity_Library_evjHaYmvKxh__b6UF5QhTTAR__SDS9ufWpogs | dynamic | compile_error:1; not_dynamically_expressible:1; reference_patch_required:1 |
| Forte__Float128_Solidity_Library_evjHaYmvKxh__kAkKE5sSeTR__tcw4bnkE3S4 | dynamic | not_dynamically_expressible:1; reference_patch_required:2 |
| Forte__Float128_Solidity_Library_evjHaYmvKxh__kAkKE5sSeTR__zQc6QMa9DZ8 | dynamic | not_dynamically_expressible:3; partial_binding:1 |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__f9M82Pw5RX4__8jhG9EGX3ao | dynamic | binding_failed:2; compile_error:4; partial_binding:3 |
| Intuition_2VUsxVJwReb__rKaU4cekpfS__TMxxnm9a7hZ | dynamic | partial_binding:2; reference_patch_required:2 |
| Morpheus_kdPtwopH6ws__frkcGbwAqGW__8JTJv9NuyVL | dynamic | compile_error:4; not_dynamically_expressible:3; reference_patch_required:1 |
| Olas_j3PRAMM3fVq__Bjv6EhkCq3j__WmGp4hG4T2w | dynamic | partial_binding:1; reference_patch_required:8 |
| Panoptic_Hypovault_c9MhophgwGP__fqM4RbqmYxf__BcLBP93xKHo | dynamic | invariant_holds_on_exploit_path:1; partial_binding:1 |
| Panoptic__Next_Core_iqcUwAhCZyD__ZSt7sSjkskQ__rdj6enAa9QN | dynamic | compile_error:1; partial_binding:8 |
| Brix_Money_qy7NXr77sDh__9zdYSJrejx4__wsQo6qFtVdZ | mixed_non_dynamic | binding_error:1; not_dynamically_expressible:1; partial_binding:2 |
| Ekubo_3FTodhsvBkM__NCCWNLzZ86f__2fRwZrwxdmF | mixed_non_dynamic | partial_binding:1; reference_patch_required:12 |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__vcmNqStwjRg__6bECv5mp6yL | mixed_non_dynamic | partial_binding:1; poc_not_witnessed:1 |
| Hybra_Finance_xo4hapwL2Jy__7RVCVStDrsF__gnqEfQdwf7p | mixed_non_dynamic | inconclusive:1; reference_patch_required:2 |
| Hybra_Finance_xo4hapwL2Jy__LJk286Uvei7__8Mfy6xJ35eR | mixed_non_dynamic | binding_failed:2; inconclusive:3 |
| Intuition_2VUsxVJwReb__6YNDfbQYkTa__KcTHtNrsMFs | mixed_non_dynamic | not_dynamically_expressible:1; reference_patch_required:1 |
| Intuition_2VUsxVJwReb__6YNDfbQYkTa__YGqgewwYA9H | mixed_non_dynamic | not_dynamically_expressible:1; partial_binding:1 |
| Intuition_2VUsxVJwReb__aayBh4TiWVT__JJJgSRQyK2f | mixed_non_dynamic | partial_binding:1; reference_patch_required:3 |
| Kinetiq_k8aVPPVguSE__Et2e5TnpUga__wHqL6oK9ToF | mixed_non_dynamic | partial_binding:3; reference_patch_required:1 |
| Olas_j3PRAMM3fVq__xAqoTentyEj__rBebLDJpU3W | mixed_non_dynamic | compile_error:5; partial_binding:1 |
| Panoptic__Next_Core_iqcUwAhCZyD__SXv7e4wnnbo__aSN55Rnh4p8 | mixed_non_dynamic | compile_error:2; partial_binding:2 |

## 3. 项目级指标

- 项目总数：20
- 至少复现 1 个 finding 的项目：19
- 项目级召回：95.0%（95% CI 76.4%–99.1%）

| 项目 | 案例 | done | 动态 | 复现 |
| --- | ---: | ---: | ---: | ---: |
| Blackhole_GUT9Y3UVuWn | 1 | 1 | 1 | 1 |
| Brix_Money_qy7NXr77sDh | 6 | 6 | 4 | 4 |
| Covenant_d4uY8y2AMSs | 6 | 6 | 6 | 4 |
| Ekubo_3FTodhsvBkM | 6 | 5 | 3 | 3 |
| Forte | 6 | 6 | 6 | 5 |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC | 6 | 6 | 4 | 4 |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn | 5 | 5 | 4 | 4 |
| Hybra_Finance_xo4hapwL2Jy | 6 | 6 | 0 | 0 |
| Intuition_2VUsxVJwReb | 5 | 5 | 1 | 1 |
| Kinetiq_k8aVPPVguSE | 6 | 6 | 3 | 3 |
| Merkl_T4ExvutBBXC | 6 | 6 | 6 | 5 |
| Monetrix_L3gNZDymiju | 6 | 6 | 5 | 5 |
| Morpheus_kdPtwopH6ws | 5 | 5 | 5 | 4 |
| Olas_j3PRAMM3fVq | 5 | 5 | 4 | 4 |
| Panoptic | 6 | 6 | 4 | 3 |
| Panoptic_Hypovault_c9MhophgwGP | 6 | 6 | 6 | 6 |
| Sequence | 6 | 6 | 6 | 6 |
| SukukFi_syLyTBz5KNA | 6 | 4 | 4 | 4 |
| Upside_xKJfM48g3oD | 2 | 2 | 2 | 2 |
| Virtuals_Protocol_hzMS6ZZkBTg | 4 | 4 | 1 | 1 |

## 4. 四指标（判例锚定口径）

| 指标 | 值 | 说明 |
| --- | ---: | --- |
| 完成率 | 97.1% | 到达 stage3 done / 全输入，95% CI 91.9%–99.0% |
| 动态终态率(覆盖率) | 71.4% | 到达复现/未复现终态 / 全输入 |
| 召回(端到端) | 67.3% | TP=68 / 判例相关样本 101，95% CI 57.7%–75.7% |
| 召回(可评测) | 91.9% | TP=68 / 判例相关动态样本 74，95% CI 83.4%–96.2% |
| 召回(端到端天花板) | 96.0% | 判例相关样本扣除 4 例机制天花板（缺参考补丁/不可动态表达）后可达上限 |
| claim级回收(复现/claim) | 30.3% | 115/380 claim，动态率 51.6%，mixed_non_dynamic 35 例 |
| 准确率(漏洞级·对外主口径) | 95.8% | TP=68 / 剔除影响不足FP后的判复现 71，95% CI 88.3%–98.6% |
| F1(漏洞级/端到端) | 0.791 | 漏洞级准确率 × 端到端召回 |
| F1(漏洞级/可评测) | 0.938 | 漏洞级准确率 × 可评测召回 |
| 准确率(机制一致性·自检) | 81.9% | TP=68 FP=15，95% CI 72.3%–88.7% |
| F1(机制一致性/端到端) | 0.739 | 一致性准确率 × 端到端召回 |
| F1(机制一致性/可评测) | 0.866 | 一致性准确率 × 可评测召回 |
| 召回(项目级) | 95.0% | 至少复现1个的项目占比，95% CI 76.4%–99.1% |
| 准确率(构造负样本·仅自检) | 100.0% | 机械TP=69 FP=0 TN=78，FP=0 是设计使然，不对外 |

### 4.1 判例锚定混淆矩阵

| 判例真值 \ 主线裁决 | 复现(+) | 未复现(-) | 合计 |
| --- | ---: | ---: | ---: |
| valid/fixed/wontfix(+) | TP=68 | FN=33 | 101 |
| invalid(-) | FP=15 | TN=60 | 75 |

> 说明：FP 采自判例 invalid 独立负样本池（75 例可评测），TP/FN 采自
> 判例相关正样本池（101 例），两池患病率不同，混淆矩阵仅展示各池内的
> 分子分母，不跨池假设等患病率。
