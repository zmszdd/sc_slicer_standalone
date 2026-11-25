# 自动召回可恢复性分层

判例有效但自动口径未复现：**38** 例

| PoC 形态 | 数量 | 自动可修性 |
| --- | ---: | --- |
| state_assert_test | 30 | 首选：绑定/快照修复 |
| revert_expected_test | 5 | 部分可修，多数走参考补丁上限 |
| other_test | 2 | 逐例判断 |
| no_body | 1 | 先补 stage2 产物 |

## 明细

| case | PoC 形态 | 最新 verdict | compile_error | UNBOUND |
| --- | --- | --- | --- | ---: |
| Ekubo_3FTodhsvBkM__TuLiGdJaxpt__2VpY9ZKEXeo | no_body | no_summary |  | 0 |
| Ekubo_3FTodhsvBkM__uPQxpkt7qin__5cvoTowJqyq | other_test | partial_binding |  | 3 |
| Hybra_Finance_xo4hapwL2Jy__F4rfhrN24eF__f549enU39vL | other_test | violation_not_reproduced |  | 1 |
| Covenant_d4uY8y2AMSs__CF5ba95T4KR__5atNeQZ3fR4 | revert_expected_test | violation_not_reproduced |  | 0 |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__7yYS2jorBMq__2vNFaZP7xME | revert_expected_test | violation_reproduced |  | 7 |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__7yYS2jorBMq__DZuT6ZLMnbC | revert_expected_test | violation_reproduced |  | 5 |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__4mNBEGcS2Q4__ABttaLoW9yp | revert_expected_test | partial_binding |  | 4 |
| Merkl_T4ExvutBBXC__si6yAc4Sp6f__ZWh59mSfE3A | revert_expected_test | effect_observed_invariant_holds |  | 0 |
| Brix_Money_qy7NXr77sDh__PGwVR6CTD6U__3hfE23tsgzG | state_assert_test | compile_error | binding_compile_failure | 4 |
| Ekubo_3FTodhsvBkM__NCCWNLzZ86f__2fRwZrwxdmF | state_assert_test | violation_not_reproduced |  | 25 |
| Ekubo_3FTodhsvBkM__NCCWNLzZ86f__CJcWnzLvufB | state_assert_test | partial_binding |  | 1 |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__B42T4SMoQbi__shfFZcbozRG | state_assert_test | violation_not_reproduced |  | 0 |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__BGmNvkuaaVZ__8hsT5afhmcc | state_assert_test | violation_not_reproduced |  | 0 |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__pa62Ux3Rpwx__T46wzJmNNeL | state_assert_test | binding_error |  | 2 |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__iU33HtdRwMc__KLN6ovWUQPG | state_assert_test | not_dynamically_expressible | not_dynamically_expressible | 0 |
| Intuition_2VUsxVJwReb__6YNDfbQYkTa__2eVNL5tctSs | state_assert_test | compile_error | binding_compile_failure | 0 |
| Intuition_2VUsxVJwReb__6YNDfbQYkTa__YGqgewwYA9H | state_assert_test | partial_binding |  | 3 |
| Intuition_2VUsxVJwReb__6YNDfbQYkTa__gK2BEnhG2WW | state_assert_test | compile_error | binding_compile_failure | 0 |
| Intuition_2VUsxVJwReb__6YNDfbQYkTa__gqqZ27wsEBG | state_assert_test | partial_binding |  | 9 |
| Intuition_2VUsxVJwReb__aayBh4TiWVT__JJJgSRQyK2f | state_assert_test | binding_error |  | 4 |
| Intuition_2VUsxVJwReb__aayBh4TiWVT__deVmwC5DHi7 | state_assert_test | reference_patch_required |  | 1 |
| Intuition_2VUsxVJwReb__aayBh4TiWVT__ew8CJcw27f8 | state_assert_test | partial_binding |  | 8 |
| Kinetiq_k8aVPPVguSE__NozCq8ZgtXD__FDynmFEjvGw | state_assert_test | preconditions_infeasible_on_code |  | 0 |
| Kinetiq_k8aVPPVguSE__PbaJqwXvgF8__LBydEn7bqih | state_assert_test | reference_patch_required |  | 1 |
| Merkl_T4ExvutBBXC__kvqzFvQzjLT__oZ5QfKLruex | state_assert_test | reference_patch_required |  | 0 |
| Monetrix_L3gNZDymiju__XdnQZTBJovh__ckuTxYrFvYX | state_assert_test | inconclusive |  | 1 |
| Morpheus_kdPtwopH6ws__HiE7tespTT5__kYHHiGvqEun | state_assert_test | partial_binding |  | 4 |
| Olas_j3PRAMM3fVq__9eKVuFn3L2m__taj2jL9umRp | state_assert_test | binding_error |  | 2 |
| Olas_j3PRAMM3fVq__xAqoTentyEj__rBebLDJpU3W | state_assert_test | effect_observed_invariant_holds |  | 0 |
| Panoptic__Next_Core_iqcUwAhCZyD__SXv7e4wnnbo__aSN55Rnh4p8 | state_assert_test | compile_error | binding_compile_failure | 1 |
| Panoptic__Next_Core_iqcUwAhCZyD__tada4pGbB9R__9eoaAimnbnD | state_assert_test | effect_observed_invariant_holds |  | 0 |
| Sequence__Transaction_Rails_Yn6A3eYizcQ__7rSTe38xKPK__hqm4CJJttHi | state_assert_test | partial_binding |  | 2 |
| SukukFi_syLyTBz5KNA__6N4VUdiTEaa__KifNto4WY2x | state_assert_test | effect_observed_invariant_holds |  | 0 |
| SukukFi_syLyTBz5KNA__6N4VUdiTEaa__UrvkNAfX6Ff | state_assert_test | effect_observed_invariant_holds |  | 0 |
| SukukFi_syLyTBz5KNA__SZy2Ly7Y3Cu__XHULcuBwgFG | state_assert_test | preconditions_infeasible_on_code |  | 0 |
| SukukFi_syLyTBz5KNA__x8fhQug5RF4__qYjoqF9WCdt | state_assert_test | effect_observed_invariant_holds |  | 0 |
| Virtuals_Protocol_hzMS6ZZkBTg__uRCNRZgiUjz__j6HuVHjfaBC | state_assert_test | partial_binding |  | 3 |
| Virtuals_Protocol_hzMS6ZZkBTg__yc36fBWWe3H__jrMhUzQFvnU | state_assert_test | effect_observed_invariant_holds |  | 0 |
