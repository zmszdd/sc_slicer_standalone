# 复现失败（FN）根因分层

判例有效但未复现：**35** 例

| 根因 | 数量 |
| --- | ---: |
| mixed_non_dynamic | 13 |
| partial_binding | 7 |
| poc_not_witnessed | 4 |
| inconclusive | 3 |
| invariant_holds_on_exploit_path | 3 |
| not_dynamically_expressible | 2 |
| patch_no_effect | 1 |
| reference_patch_required | 1 |
| stage2:no_stage2_run | 1 |

## 明细

| case | 根因 | claim 级拆分 |
| --- | --- | --- |
| Hybra_Finance_xo4hapwL2Jy__XgPnfi6S3qh__TJzbsr7Tbkg | inconclusive | inconclusive:2 |
| Hybra_Finance_xo4hapwL2Jy__jegipCJB5Kv__dQUWyfXRnAP | inconclusive | inconclusive:12 |
| Virtuals_Protocol_hzMS6ZZkBTg__bp8cZknNbnC__eSjbpXjKeUJ | inconclusive | inconclusive:4 |
| Merkl_T4ExvutBBXC__V6VRqYmA4BA__MZCDvNevrjd | invariant_holds_on_exploit_path | invariant_holds_on_exploit_path:1 |
| Morpheus_kdPtwopH6ws__frkcGbwAqGW__cWxqBprb2Ss | invariant_holds_on_exploit_path | invariant_holds_on_exploit_path:2 |
| Virtuals_Protocol_hzMS6ZZkBTg__yc36fBWWe3H__jrMhUzQFvnU | invariant_holds_on_exploit_path | invariant_holds_on_exploit_path:1 |
| Brix_Money_qy7NXr77sDh__9zdYSJrejx4__wsQo6qFtVdZ | mixed_non_dynamic | binding_error:1; not_dynamically_expressible:1; partial_binding:2 |
| Ekubo_3FTodhsvBkM__NCCWNLzZ86f__2fRwZrwxdmF | mixed_non_dynamic | partial_binding:1; reference_patch_required:12 |
| Forte__Float128_Solidity_Library_evjHaYmvKxh__kAkKE5sSeTR__G9JhCyBVTcC | mixed_non_dynamic | not_dynamically_expressible:1; poc_not_witnessed:1 |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__vcmNqStwjRg__6bECv5mp6yL | mixed_non_dynamic | partial_binding:1; poc_not_witnessed:1 |
| Hybra_Finance_xo4hapwL2Jy__7RVCVStDrsF__gnqEfQdwf7p | mixed_non_dynamic | inconclusive:1; reference_patch_required:2 |
| Hybra_Finance_xo4hapwL2Jy__LJk286Uvei7__8Mfy6xJ35eR | mixed_non_dynamic | binding_failed:2; inconclusive:3 |
| Intuition_2VUsxVJwReb__6YNDfbQYkTa__KcTHtNrsMFs | mixed_non_dynamic | not_dynamically_expressible:1; reference_patch_required:1 |
| Intuition_2VUsxVJwReb__6YNDfbQYkTa__YGqgewwYA9H | mixed_non_dynamic | not_dynamically_expressible:1; partial_binding:1 |
| Intuition_2VUsxVJwReb__aayBh4TiWVT__JJJgSRQyK2f | mixed_non_dynamic | partial_binding:1; reference_patch_required:3 |
| Kinetiq_k8aVPPVguSE__Et2e5TnpUga__wHqL6oK9ToF | mixed_non_dynamic | partial_binding:3; reference_patch_required:1 |
| Olas_j3PRAMM3fVq__xAqoTentyEj__rBebLDJpU3W | mixed_non_dynamic | compile_error:5; partial_binding:1 |
| Panoptic__Next_Core_iqcUwAhCZyD__AA46LPa6pbL__dV9PDL3VJ3m | mixed_non_dynamic | compile_error:3; poc_not_witnessed:3 |
| Panoptic__Next_Core_iqcUwAhCZyD__SXv7e4wnnbo__aSN55Rnh4p8 | mixed_non_dynamic | compile_error:2; partial_binding:2 |
| Hybra_Finance_xo4hapwL2Jy__F4rfhrN24eF__f549enU39vL | not_dynamically_expressible | not_dynamically_expressible:1 |
| Kinetiq_k8aVPPVguSE__YdUkynebFvW__FCU4bMUR3hY | not_dynamically_expressible | not_dynamically_expressible:2 |
| Blackhole_GUT9Y3UVuWn__ZyhZwQzWzbf__bc6LVb2Kvjn | partial_binding | partial_binding:2 |
| Brix_Money_qy7NXr77sDh__PGwVR6CTD6U__5pt4vrEZuyz | partial_binding | partial_binding:4 |
| Ekubo_3FTodhsvBkM__uPQxpkt7qin__5cvoTowJqyq | partial_binding | partial_binding:1 |
| Hybra_Finance_xo4hapwL2Jy__fsfqfuE2eMf__nb9hn2hBQ2b | partial_binding | partial_binding:1 |
| Monetrix_L3gNZDymiju__vbdhAfq36PC__NaDr87ezifs | partial_binding | partial_binding:3 |
| Panoptic__Next_Core_iqcUwAhCZyD__CUEQdPu878N__ayGYSR98MV8 | partial_binding | partial_binding:1 |
| Virtuals_Protocol_hzMS6ZZkBTg__uRCNRZgiUjz__j6HuVHjfaBC | partial_binding | partial_binding:1 |
| Ekubo_3FTodhsvBkM__NCCWNLzZ86f__bKb5Sm2R6Jq | patch_no_effect | patch_no_effect:1 |
| Covenant_d4uY8y2AMSs__CF5ba95T4KR__5atNeQZ3fR4 | poc_not_witnessed | poc_not_witnessed:2 |
| Covenant_d4uY8y2AMSs__otmbJXz4irq__h23uU6Ai3Mx | poc_not_witnessed | poc_not_witnessed:1 |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__FbQktkofz8X__yG32SUkqYGK | poc_not_witnessed | poc_not_witnessed:1 |
| Kinetiq_k8aVPPVguSE__bP38mw3SCq2__eEvYodNRrvz | poc_not_witnessed | poc_not_witnessed:1 |
| Intuition_2VUsxVJwReb__aayBh4TiWVT__7YSswxrdK8D | reference_patch_required | reference_patch_required:2 |
| Ekubo_3FTodhsvBkM__TuLiGdJaxpt__2VpY9ZKEXeo | stage2:no_stage2_run |  |
