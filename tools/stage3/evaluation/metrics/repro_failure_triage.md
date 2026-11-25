# 复现失败（FN）根因分层

判例有效但未复现：**38** 例

| 根因 | 数量 |
| --- | ---: |
| mixed_non_dynamic | 17 |
| partial_binding | 12 |
| invariant_holds_on_exploit_path | 3 |
| not_dynamically_expressible | 2 |
| poc_not_witnessed | 2 |
| stage2:no_stage2_run | 1 |
| compile_error | 1 |

## 明细

| case | 根因 | claim 级拆分 |
| --- | --- | --- |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__B42T4SMoQbi__shfFZcbozRG | compile_error | compile_error:2 |
| SukukFi_syLyTBz5KNA__6N4VUdiTEaa__KifNto4WY2x | invariant_holds_on_exploit_path | invariant_holds_on_exploit_path:2 |
| SukukFi_syLyTBz5KNA__x8fhQug5RF4__qYjoqF9WCdt | invariant_holds_on_exploit_path | invariant_holds_on_exploit_path:1 |
| Virtuals_Protocol_hzMS6ZZkBTg__yc36fBWWe3H__jrMhUzQFvnU | invariant_holds_on_exploit_path | invariant_holds_on_exploit_path:1 |
| Brix_Money_qy7NXr77sDh__PGwVR6CTD6U__3hfE23tsgzG | mixed_non_dynamic | binding_error:1; compile_error:4; invariant_holds_on_exploit_path:2; partial_binding:5 |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__7yYS2jorBMq__2vNFaZP7xME | mixed_non_dynamic | binding_error:1; partial_binding:1 |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__BGmNvkuaaVZ__8hsT5afhmcc | mixed_non_dynamic | compile_error:1; invariant_holds_on_exploit_path:2; partial_binding:1 |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__pa62Ux3Rpwx__T46wzJmNNeL | mixed_non_dynamic | binding_error:1; partial_binding:1 |
| Intuition_2VUsxVJwReb__6YNDfbQYkTa__2eVNL5tctSs | mixed_non_dynamic | binding_error:1; not_dynamically_expressible:1 |
| Intuition_2VUsxVJwReb__6YNDfbQYkTa__YGqgewwYA9H | mixed_non_dynamic | not_dynamically_expressible:1; partial_binding:1 |
| Intuition_2VUsxVJwReb__aayBh4TiWVT__JJJgSRQyK2f | mixed_non_dynamic | partial_binding:1; reference_patch_required:3 |
| Intuition_2VUsxVJwReb__aayBh4TiWVT__deVmwC5DHi7 | mixed_non_dynamic | compile_error:1; partial_binding:1 |
| Kinetiq_k8aVPPVguSE__PbaJqwXvgF8__LBydEn7bqih | mixed_non_dynamic | compile_error:1; partial_binding:2 |
| Merkl_T4ExvutBBXC__kvqzFvQzjLT__oZ5QfKLruex | mixed_non_dynamic | compile_error:1; invariant_holds_on_exploit_path:1 |
| Merkl_T4ExvutBBXC__si6yAc4Sp6f__ZWh59mSfE3A | mixed_non_dynamic | invariant_holds_on_exploit_path:1; poc_not_witnessed:1 |
| Monetrix_L3gNZDymiju__XdnQZTBJovh__ckuTxYrFvYX | mixed_non_dynamic | binding_error:1; compile_error:1; inconclusive:1; invariant_holds_on_exploit_path:1; partial_binding:2 |
| Olas_j3PRAMM3fVq__9eKVuFn3L2m__taj2jL9umRp | mixed_non_dynamic | compile_error:1; partial_binding:1 |
| Olas_j3PRAMM3fVq__xAqoTentyEj__rBebLDJpU3W | mixed_non_dynamic | compile_error:5; partial_binding:1 |
| Panoptic__Next_Core_iqcUwAhCZyD__SXv7e4wnnbo__aSN55Rnh4p8 | mixed_non_dynamic | compile_error:2; not_dynamically_expressible:1; partial_binding:1 |
| Sequence__Transaction_Rails_Yn6A3eYizcQ__7rSTe38xKPK__hqm4CJJttHi | mixed_non_dynamic | binding_error:2; partial_binding:2 |
| SukukFi_syLyTBz5KNA__6N4VUdiTEaa__UrvkNAfX6Ff | mixed_non_dynamic | invariant_holds_on_exploit_path:1; patch_no_effect:1 |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__iU33HtdRwMc__KLN6ovWUQPG | not_dynamically_expressible | not_dynamically_expressible:2 |
| Hybra_Finance_xo4hapwL2Jy__F4rfhrN24eF__f549enU39vL | not_dynamically_expressible | not_dynamically_expressible:1 |
| Ekubo_3FTodhsvBkM__NCCWNLzZ86f__2fRwZrwxdmF | partial_binding | partial_binding:13 |
| Ekubo_3FTodhsvBkM__NCCWNLzZ86f__CJcWnzLvufB | partial_binding | partial_binding:2 |
| Ekubo_3FTodhsvBkM__uPQxpkt7qin__5cvoTowJqyq | partial_binding | partial_binding:1 |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__7yYS2jorBMq__DZuT6ZLMnbC | partial_binding | partial_binding:3 |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__4mNBEGcS2Q4__ABttaLoW9yp | partial_binding | partial_binding:2 |
| Intuition_2VUsxVJwReb__6YNDfbQYkTa__gK2BEnhG2WW | partial_binding | partial_binding:2 |
| Intuition_2VUsxVJwReb__6YNDfbQYkTa__gqqZ27wsEBG | partial_binding | partial_binding:3 |
| Intuition_2VUsxVJwReb__aayBh4TiWVT__ew8CJcw27f8 | partial_binding | partial_binding:4 |
| Kinetiq_k8aVPPVguSE__NozCq8ZgtXD__FDynmFEjvGw | partial_binding | partial_binding:1 |
| Morpheus_kdPtwopH6ws__HiE7tespTT5__kYHHiGvqEun | partial_binding | partial_binding:2 |
| Panoptic__Next_Core_iqcUwAhCZyD__tada4pGbB9R__9eoaAimnbnD | partial_binding | partial_binding:1 |
| Virtuals_Protocol_hzMS6ZZkBTg__uRCNRZgiUjz__j6HuVHjfaBC | partial_binding | partial_binding:1 |
| Covenant_d4uY8y2AMSs__CF5ba95T4KR__5atNeQZ3fR4 | poc_not_witnessed | poc_not_witnessed:2 |
| SukukFi_syLyTBz5KNA__SZy2Ly7Y3Cu__XHULcuBwgFG | poc_not_witnessed | poc_not_witnessed:4 |
| Ekubo_3FTodhsvBkM__TuLiGdJaxpt__2VpY9ZKEXeo | stage2:no_stage2_run |  |
