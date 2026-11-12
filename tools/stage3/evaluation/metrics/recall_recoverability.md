# 自动召回可恢复性分层

判例有效但自动口径未复现：**42** 例

| PoC 形态 | 数量 | 自动可修性 |
| --- | ---: | --- |
| state_assert_test | 17 | 首选：绑定/快照修复 |
| revert_expected_test | 16 | 部分可修，多数走参考补丁上限 |
| other_test | 8 | 逐例判断 |
| no_body | 1 | 先补 stage2 产物 |

## 明细

| case | PoC 形态 | 最新 verdict | compile_error | UNBOUND |
| --- | --- | --- | --- | ---: |
| Ekubo_3FTodhsvBkM__TuLiGdJaxpt__2VpY9ZKEXeo | no_body | no_summary |  | 0 |
| Covenant_d4uY8y2AMSs__otmbJXz4irq__h23uU6Ai3Mx | other_test | violation_not_reproduced |  | 0 |
| Ekubo_3FTodhsvBkM__uPQxpkt7qin__5cvoTowJqyq | other_test | partial_binding |  | 3 |
| Hybra_Finance_xo4hapwL2Jy__F4rfhrN24eF__f549enU39vL | other_test | not_dynamically_expressible | not_dynamically_expressible | 1 |
| Hybra_Finance_xo4hapwL2Jy__fsfqfuE2eMf__nb9hn2hBQ2b | other_test | partial_binding |  | 0 |
| Hybra_Finance_xo4hapwL2Jy__jegipCJB5Kv__dQUWyfXRnAP | other_test | inconclusive |  | 9 |
| Intuition_2VUsxVJwReb__6YNDfbQYkTa__KcTHtNrsMFs | other_test | not_dynamically_expressible | not_dynamically_expressible | 4 |
| Panoptic__Next_Core_iqcUwAhCZyD__ZSt7sSjkskQ__rdj6enAa9QN | other_test | compile_error | binding_compile_failure | 5 |
| Virtuals_Protocol_hzMS6ZZkBTg__bp8cZknNbnC__eSjbpXjKeUJ | other_test | inconclusive |  | 0 |
| Blackhole_GUT9Y3UVuWn__ZyhZwQzWzbf__bc6LVb2Kvjn | revert_expected_test | effect_observed_invariant_holds |  | 4 |
| Brix_Money_qy7NXr77sDh__9zdYSJrejx4__wsQo6qFtVdZ | revert_expected_test | binding_error |  | 3 |
| Brix_Money_qy7NXr77sDh__PGwVR6CTD6U__5pt4vrEZuyz | revert_expected_test | partial_binding |  | 0 |
| Covenant_d4uY8y2AMSs__CF5ba95T4KR__5atNeQZ3fR4 | revert_expected_test | not_dynamically_expressible | not_dynamically_expressible | 1 |
| Ekubo_3FTodhsvBkM__NCCWNLzZ86f__2fRwZrwxdmF | revert_expected_test | reference_patch_required |  | 15 |
| Ekubo_3FTodhsvBkM__NCCWNLzZ86f__bKb5Sm2R6Jq | revert_expected_test | preconditions_infeasible_on_code |  | 0 |
| Forte__Float128_Solidity_Library_evjHaYmvKxh__kAkKE5sSeTR__G9JhCyBVTcC | revert_expected_test | not_dynamically_expressible | not_dynamically_expressible | 0 |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__vcmNqStwjRg__6bECv5mp6yL | revert_expected_test | partial_binding |  | 3 |
| Hybra_Finance_xo4hapwL2Jy__XgPnfi6S3qh__TJzbsr7Tbkg | revert_expected_test | inconclusive |  | 2 |
| Kinetiq_k8aVPPVguSE__YdUkynebFvW__FCU4bMUR3hY | revert_expected_test | not_dynamically_expressible | not_dynamically_expressible | 6 |
| Merkl_T4ExvutBBXC__V6VRqYmA4BA__MZCDvNevrjd | revert_expected_test | violation_not_reproduced |  | 0 |
| Monetrix_L3gNZDymiju__R52fkgDFn8b__KCWcn8VxtxH | revert_expected_test | preconditions_infeasible_on_code |  | 0 |
| Monetrix_L3gNZDymiju__vbdhAfq36PC__7jNrRNx2J4R | revert_expected_test | partial_binding |  | 3 |
| Monetrix_L3gNZDymiju__vbdhAfq36PC__NaDr87ezifs | revert_expected_test | partial_binding |  | 4 |
| Morpheus_kdPtwopH6ws__frkcGbwAqGW__8JTJv9NuyVL | revert_expected_test | violation_reproduced |  | 0 |
| Morpheus_kdPtwopH6ws__frkcGbwAqGW__cWxqBprb2Ss | revert_expected_test | violation_not_reproduced |  | 0 |
| Forte__Float128_Solidity_Library_evjHaYmvKxh__hAkTyQBGSaf__bwhnxX2MhLd | state_assert_test | violation_reproduced |  | 0 |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__FbQktkofz8X__yG32SUkqYGK | state_assert_test | preconditions_infeasible_on_code |  | 0 |
| Hybra_Finance_xo4hapwL2Jy__7RVCVStDrsF__gnqEfQdwf7p | state_assert_test | reference_patch_required |  | 0 |
| Hybra_Finance_xo4hapwL2Jy__LJk286Uvei7__8Mfy6xJ35eR | state_assert_test | inconclusive |  | 0 |
| Intuition_2VUsxVJwReb__6YNDfbQYkTa__YGqgewwYA9H | state_assert_test | not_dynamically_expressible | not_dynamically_expressible | 4 |
| Intuition_2VUsxVJwReb__aayBh4TiWVT__7YSswxrdK8D | state_assert_test | reference_patch_required |  | 0 |
| Intuition_2VUsxVJwReb__aayBh4TiWVT__JJJgSRQyK2f | state_assert_test | reference_patch_required |  | 4 |
| Kinetiq_k8aVPPVguSE__Et2e5TnpUga__wHqL6oK9ToF | state_assert_test | reference_patch_required |  | 0 |
| Kinetiq_k8aVPPVguSE__bP38mw3SCq2__eEvYodNRrvz | state_assert_test | preconditions_infeasible_on_code |  | 0 |
| Morpheus_kdPtwopH6ws__siuCvb42gBS__299CV6kMKS8 | state_assert_test | violation_reproduced |  | 0 |
| Olas_j3PRAMM3fVq__X5pVGjLL6cP__z9kxZbTyPit | state_assert_test | reference_patch_required |  | 8 |
| Olas_j3PRAMM3fVq__xAqoTentyEj__rBebLDJpU3W | state_assert_test | compile_error | binding_compile_failure | 0 |
| Panoptic__Next_Core_iqcUwAhCZyD__AA46LPa6pbL__dV9PDL3VJ3m | state_assert_test | compile_error | binding_compile_failure | 0 |
| Panoptic__Next_Core_iqcUwAhCZyD__CUEQdPu878N__ayGYSR98MV8 | state_assert_test | partial_binding |  | 2 |
| Panoptic__Next_Core_iqcUwAhCZyD__SXv7e4wnnbo__aSN55Rnh4p8 | state_assert_test | compile_error | binding_compile_failure | 3 |
| Virtuals_Protocol_hzMS6ZZkBTg__uRCNRZgiUjz__j6HuVHjfaBC | state_assert_test | partial_binding |  | 3 |
| Virtuals_Protocol_hzMS6ZZkBTg__yc36fBWWe3H__jrMhUzQFvnU | state_assert_test | effect_observed_invariant_holds |  | 0 |
