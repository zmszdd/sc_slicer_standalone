# 主口径逐例可评测状态审计

- 样本：`mainline_sample_mini.json`，40 正例 + 40 负例。
- 判定与 `mainline_metrics.py` 使用同一 current-protocol evidence 规则。
- 未评测案例绝不进入混淆矩阵；这里只解释“为什么未评测”。

| 标签 | eligible | total | coverage |
| --- | ---: | ---: | ---: |
| positive | 35 | 40 | 87.5% |
| negative | 10 | 40 | 25.0% |

| 标签 | status | cases |
| --- | --- | ---: |
| positive | `eligible` | 35 |
| positive | `not_run` | 4 |
| positive | `stage2_blocked` | 1 |
| negative | `eligible` | 10 |
| negative | `not_run` | 16 |
| negative | `run_unresolved` | 14 |

## 未评测阻塞原因

| 标签 | reason | cases |
| --- | --- | ---: |
| positive | `core_piv_not_fully_formalized` | 1 |
| positive | `no_stage3_run` | 4 |
| negative | `binding_error` | 2 |
| negative | `compile_error` | 2 |
| negative | `effect_not_witnessed` | 2 |
| negative | `negative_witness_ineligible` | 1 |
| negative | `no_slice` | 16 |
| negative | `partial_binding` | 5 |
| negative | `reference_patch_required` | 1 |
| negative | `stage2_restatement_required` | 1 |

## 逐例明细

| case | label | status | reason | next_action |
| --- | --- | --- | --- | --- |
| Hybra_Finance_xo4hapwL2Jy__PzD5FbkNA5e__YAoPVKDcekp | positive | `eligible` | `effect_observed_invariant_holds` | `none` |
| Intuition_2VUsxVJwReb__vtU4cDUiiDR__ay9UKTHDhrG | positive | `eligible` | `positive_unresolved_counted_fn` | `none` |
| Hybra_Finance_xo4hapwL2Jy__XgPnfi6S3qh__K5hvaZWagxN | positive | `eligible` | `positive_unresolved_counted_fn` | `none` |
| SukukFi_syLyTBz5KNA__SZy2Ly7Y3Cu__VcuomLx35E9 | positive | `eligible` | `effect_not_witnessed` | `none` |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__QW9maHr29yd__sRR6R7uhY36 | positive | `eligible` | `positive_unresolved_counted_fn` | `none` |
| Hybra_Finance_xo4hapwL2Jy__sZ4HDx3uzNd__GKcn5Fwh5zG | positive | `stage2_blocked` | `core_piv_not_fully_formalized` | `fix_stage2_core_piv_not_fully_formalized` |
| Panoptic_Hypovault_c9MhophgwGP__fqM4RbqmYxf__gK7S6y7Fz7K | positive | `eligible` | `effect_observed_invariant_holds` | `none` |
| Panoptic__Next_Core_iqcUwAhCZyD__x6YHGbxHmh9__BCsgBaTYsPa | positive | `eligible` | `positive_unresolved_counted_fn` | `none` |
| Olas_j3PRAMM3fVq__9eKVuFn3L2m__o7uYLjquEzf | positive | `not_run` | `no_stage3_run` | `run_stage3` |
| Merkl_T4ExvutBBXC__9JnmzBSjjfp__SuKXTvLqrK5 | positive | `eligible` | `positive_unresolved_counted_fn` | `none` |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__WxFog2dKdF8__p6eD3ePCaoh | positive | `not_run` | `no_stage3_run` | `run_stage3` |
| Merkl_T4ExvutBBXC__kvqzFvQzjLT__ADxTy9Ma6wN | positive | `eligible` | `violation_reproduced` | `none` |
| Monetrix_L3gNZDymiju__XdnQZTBJovh__ncvmdYkfAtq | positive | `eligible` | `positive_unresolved_counted_fn` | `none` |
| Monetrix_L3gNZDymiju__vbdhAfq36PC__KYKEdg3wHRs | positive | `eligible` | `positive_unresolved_counted_fn` | `none` |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__qFXS4TWRDTc__dHyYZoKzTEW | positive | `eligible` | `positive_unresolved_counted_fn` | `none` |
| Hybra_Finance_xo4hapwL2Jy__7LKTwwSAteH__oX4gqWn5JPV | positive | `eligible` | `positive_unresolved_counted_fn` | `none` |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__iU33HtdRwMc__RkM8RHjiMUM | positive | `eligible` | `violation_reproduced` | `none` |
| SukukFi_syLyTBz5KNA__SZy2Ly7Y3Cu__YH6C6DWksVe | positive | `eligible` | `violation_reproduced` | `none` |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__4mNBEGcS2Q4__i74QjxE4Y98 | positive | `eligible` | `effect_not_witnessed` | `none` |
| Intuition_2VUsxVJwReb__aayBh4TiWVT__5gEysuN9QMh | positive | `eligible` | `positive_unresolved_counted_fn` | `none` |
| Ekubo_3FTodhsvBkM__dtK3s8JSnTx__QCyardr6BSH | positive | `eligible` | `positive_unresolved_counted_fn` | `none` |
| SukukFi_syLyTBz5KNA__6N4VUdiTEaa__ScVqnBqSyyG | positive | `eligible` | `positive_unresolved_counted_fn` | `none` |
| SukukFi_syLyTBz5KNA__SZy2Ly7Y3Cu__hDxUg7kc8rW | positive | `eligible` | `violation_reproduced` | `none` |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__B42T4SMoQbi__DrxMNRA5RNZ | positive | `eligible` | `positive_unresolved_counted_fn` | `none` |
| Intuition_2VUsxVJwReb__6YNDfbQYkTa__WkKHsgbnsYK | positive | `eligible` | `positive_unresolved_counted_fn` | `none` |
| Intuition_2VUsxVJwReb__iBf2zd3uGQB__tGEDgW5YXhi | positive | `eligible` | `fingerprinted_terminal_result` | `none` |
| Sequence__Transaction_Rails_Yn6A3eYizcQ__7rSTe38xKPK__hCd5TRkgJwD | positive | `eligible` | `positive_unresolved_counted_fn` | `none` |
| Sequence__Transaction_Rails_Yn6A3eYizcQ__7rSTe38xKPK__uaBoVFLvr85 | positive | `eligible` | `positive_unresolved_counted_fn` | `none` |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__Xrgn2WT5sTG__LG47BL6gFZR | positive | `eligible` | `positive_unresolved_counted_fn` | `none` |
| Hybra_Finance_xo4hapwL2Jy__7RVCVStDrsF__YFfbDGPYnUz | positive | `eligible` | `positive_unresolved_counted_fn` | `none` |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__qFXS4TWRDTc__mXqGeRvWuCf | positive | `not_run` | `no_stage3_run` | `run_stage3` |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__LPhijqJeGx2__iikf7iAzHKQ | positive | `eligible` | `positive_unresolved_counted_fn` | `none` |
| Panoptic__Next_Core_iqcUwAhCZyD__CUEQdPu878N__ziD3Nd27Ynb | positive | `eligible` | `positive_unresolved_counted_fn` | `none` |
| Panoptic__Next_Core_iqcUwAhCZyD__CUEQdPu878N__TLnoWTYjws5 | positive | `eligible` | `positive_unresolved_counted_fn` | `none` |
| Panoptic__Next_Core_iqcUwAhCZyD__e2fEpq8wpgw__R8PJPMxPpk9 | positive | `eligible` | `positive_unresolved_counted_fn` | `none` |
| SukukFi_syLyTBz5KNA__DkPdxd8nA3n__Zrash2sFL9M | positive | `not_run` | `no_stage3_run` | `run_stage3` |
| Brix_Money_qy7NXr77sDh__Nxh87eHBt9G__hX7p7s459Aw | positive | `eligible` | `positive_unresolved_counted_fn` | `none` |
| Olas_j3PRAMM3fVq__9eKVuFn3L2m__GAp2htd92t9 | positive | `eligible` | `violation_reproduced` | `none` |
| Panoptic_Hypovault_c9MhophgwGP__MoUD6X4jmfD__iyZgPPcErvD | positive | `eligible` | `effect_observed_invariant_holds` | `none` |
| Covenant_d4uY8y2AMSs__zTAab6iGGZx__Dxst84uDVNZ | positive | `eligible` | `positive_unresolved_counted_fn` | `none` |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__W3F7ikgZG3G__MDvgv55V6yC | negative | `not_run` | `no_slice` | `build_negative_witness_slice` |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__ajDovMJcy4Z__VnHTm6D7Vbu | negative | `run_unresolved` | `partial_binding` | `rebind` |
| Olas_j3PRAMM3fVq__3yEE4KaYdfx__WNZNWFgB3Kn | negative | `not_run` | `no_slice` | `build_negative_witness_slice` |
| Upside_xKJfM48g3oD__svXKMnnAFqb__kNHMhbX6Xqc | negative | `not_run` | `no_slice` | `build_negative_witness_slice` |
| SukukFi_syLyTBz5KNA__eJytFti7FNb__kWitmT5thJT | negative | `run_unresolved` | `stage2_restatement_required` | `fix_stage2` |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__rNLC57pRsAp__xuTQrt73NLC | negative | `run_unresolved` | `negative_witness_ineligible` | `restore_negative_witness_then_rerun` |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__jSZeTF7Qoug__WH5cHLf6NzX | negative | `not_run` | `no_slice` | `build_negative_witness_slice` |
| Olas_j3PRAMM3fVq__ARScRuAhv7j__BUxmxhf6cQP | negative | `not_run` | `no_slice` | `build_negative_witness_slice` |
| SukukFi_syLyTBz5KNA__A78JaZeDQAg__GXkzLPpwfjt | negative | `run_unresolved` | `partial_binding` | `rebind` |
| Kinetiq_k8aVPPVguSE__ebbaGD7Ucod__vY6yzLcR42f | negative | `eligible` | `effect_observed_invariant_holds` | `none` |
| Olas_j3PRAMM3fVq__3yEE4KaYdfx__8oYyHrFaoqq | negative | `not_run` | `no_slice` | `build_negative_witness_slice` |
| Kinetiq_k8aVPPVguSE__MbpYs4bFuam__9CXcSBjpXnP | negative | `run_unresolved` | `binding_error` | `rebind` |
| Olas_j3PRAMM3fVq__ARScRuAhv7j__63oaDWW846Z | negative | `run_unresolved` | `partial_binding` | `rebind` |
| Olas_j3PRAMM3fVq__3yEE4KaYdfx__uZYYYKCBXLp | negative | `not_run` | `no_slice` | `build_negative_witness_slice` |
| Kinetiq_k8aVPPVguSE__ebbaGD7Ucod__XrKUnz7UWSy | negative | `eligible` | `effect_observed_invariant_holds` | `none` |
| SukukFi_syLyTBz5KNA__eJytFti7FNb__Rgkj753sdoV | negative | `run_unresolved` | `effect_not_witnessed` | `resolve_effect_witness_then_rerun` |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__xK7NZycdpFR__Mn6UhkGqwKg | negative | `eligible` | `effect_observed_invariant_holds` | `none` |
| Olas_j3PRAMM3fVq__ARScRuAhv7j__6fxNSEnixLe | negative | `run_unresolved` | `reference_patch_required` | `provide_reference_patch` |
| Kinetiq_k8aVPPVguSE__ebbaGD7Ucod__4DNu4EkJqs3 | negative | `eligible` | `violation_reproduced` | `none` |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__W3F7ikgZG3G__XewKKTqihQw | negative | `run_unresolved` | `binding_error` | `rebind` |
| Blackhole_GUT9Y3UVuWn__AjVzbe6gFbF__a9MqcaprTF9 | negative | `eligible` | `effect_observed_invariant_holds` | `none` |
| Virtuals_Protocol_hzMS6ZZkBTg__h4PpBUYhjDo__v4JpqEeCiz4 | negative | `not_run` | `no_slice` | `build_negative_witness_slice` |
| Upside_xKJfM48g3oD__LLchkS5m59s__RCULV7kmScS | negative | `not_run` | `no_slice` | `build_negative_witness_slice` |
| Olas_j3PRAMM3fVq__qjoyAom3FSt__ao3Y7v5VC2r | negative | `not_run` | `no_slice` | `build_negative_witness_slice` |
| SukukFi_syLyTBz5KNA__A78JaZeDQAg__KB43a2xjTpE | negative | `run_unresolved` | `partial_binding` | `rebind` |
| Kinetiq_k8aVPPVguSE__MbpYs4bFuam__YBqcxLs7RZ8 | negative | `not_run` | `no_slice` | `build_negative_witness_slice` |
| SukukFi_syLyTBz5KNA__eJytFti7FNb__uenFCWAv7Bb | negative | `eligible` | `effect_observed_invariant_holds` | `none` |
| Upside_xKJfM48g3oD__LLchkS5m59s__mxocxy3YEHF | negative | `not_run` | `no_slice` | `build_negative_witness_slice` |
| Ekubo_3FTodhsvBkM__zgk7ckWuUhC__mgTBBLsxXZg | negative | `run_unresolved` | `partial_binding` | `rebind` |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__KNY9V8k9X7b__FLB4c97eys2 | negative | `not_run` | `no_slice` | `build_negative_witness_slice` |
| Panoptic_Next_Core_iqcUwAhCZyD__Rw2FgSMX67N__VkPsapRC4YC | negative | `not_run` | `no_slice` | `build_negative_witness_slice` |
| Kinetiq_k8aVPPVguSE__ebbaGD7Ucod__5JBt88KYa4w | negative | `eligible` | `effect_observed_invariant_holds` | `none` |
| SukukFi_syLyTBz5KNA__eJytFti7FNb__5ytsEGz5UQp | negative | `run_unresolved` | `compile_error` | `repair_harness_then_rerun` |
| SukukFi_syLyTBz5KNA__eJytFti7FNb__y7LhXPttDHK | negative | `run_unresolved` | `effect_not_witnessed` | `resolve_effect_witness_then_rerun` |
| Panoptic_Next_Core_iqcUwAhCZyD__LLArmWJ8thu__BfMyHVGbq9v | negative | `not_run` | `no_slice` | `build_negative_witness_slice` |
| Kinetiq_k8aVPPVguSE__ebbaGD7Ucod__PPechBUVDuU | negative | `run_unresolved` | `compile_error` | `repair_harness_then_rerun` |
| Blackhole_GUT9Y3UVuWn__AjVzbe6gFbF__xDxfm9R9baA | negative | `eligible` | `effect_observed_invariant_holds` | `none` |
| Blackhole_GUT9Y3UVuWn__AjVzbe6gFbF__KZTJpnQnrRG | negative | `eligible` | `effect_observed_invariant_holds` | `none` |
| Blackhole_GUT9Y3UVuWn__Wgf3g5jbCAv__uT8YBnoVGfc | negative | `eligible` | `effect_observed_invariant_holds` | `none` |
| Panoptic_Next_Core_iqcUwAhCZyD__rqniH7kctet__W7s87xniaEA | negative | `not_run` | `no_slice` | `build_negative_witness_slice` |
