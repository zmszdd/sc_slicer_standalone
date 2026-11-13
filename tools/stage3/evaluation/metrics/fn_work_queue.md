# 自动召回 FN 工作队列

判例有效但自动口径未复现：**33** 例；可恢复 **29** / 天花板 **4**。

| 优先级 | 动作 | 数量 |
| --- | --- | ---: |
| P9 | rebind | 18 |
| P9 | stage2_rerun | 4 |
| P9 | witness_poc | 4 |
| P9 | retry_inconclusive | 3 |
| P9 | reference_patch | 4 |

## 队列

| case | 动作 | PoC 形态 | verdict | UNBOUND | 依据 |
| --- | --- | --- | --- | ---: | --- |
| Ekubo_3FTodhsvBkM__uPQxpkt7qin__5cvoTowJqyq | rebind | other_test | partial_binding | 3 | binding repairable: run stage3_verdict_loop to re-propose (['ced3e7f5f_exactin_fee_paid', 'ced3e7f5f_exactout_fee_paid', 'ced3e7f5f_paths_fee_mismatch'] UNBOUND, compile=-) |
| Intuition_2VUsxVJwReb__6YNDfbQYkTa__KcTHtNrsMFs | rebind | other_test | partial_binding | 4 | binding repairable: run stage3_verdict_loop to re-propose (['c6c0a8f28_time_window_modified_by_third_party', 'c6c0a8f28_signature_invalidated_by_modification', 'c6c0a8f28_time_window_bound_to_signature', 'c6c0a8f28_victim_userop_permanently_blocked'] UNBOUND, compile=-) |
| Brix_Money_qy7NXr77sDh__9zdYSJrejx4__wsQo6qFtVdZ | rebind | revert_expected_test | compile_error | 1 | binding repairable: run stage3_verdict_loop to re-propose (['cb327fb04_channel_permanently_blocked_for_others'] UNBOUND, compile=binding_compile_failure) |
| Brix_Money_qy7NXr77sDh__PGwVR6CTD6U__5pt4vrEZuyz | rebind | revert_expected_test | compile_error | 0 | binding repairable: run stage3_verdict_loop to re-propose (0 UNBOUND, compile=binding_compile_failure) |
| Ekubo_3FTodhsvBkM__NCCWNLzZ86f__2fRwZrwxdmF | rebind | revert_expected_test | partial_binding | 15 | binding repairable: run stage3_verdict_loop to re-propose (['c827f3dbf_nonzero_debt_count_at_lock_completion', 'ca4e0701f_nonzero_debt_count_at_lock_completion', 'cfff479f8_nonzero_debt_count_at_lock_completion', 'c8ba3f1d6_nonzero_debt_count_at_lock_completion', 'c544fa1fd_nonzero_debt_count_at_lock_completion', 'cdf81248c_nonzero_debt_count_at_lock_completion', 'cdf81248c_position_withdrawal_blocked', 'cc3ea6ab2_nonzero_debt_count_at_lock_completion', 'cb91800b1_nonzero_debt_count_at_lock_completion', 'c865f93cc_nonzero_debt_count_at_lock_completion', 'c85ff672d_nonzero_debt_count_at_lock_completion', 'c6b8782eb_nonzero_debt_count_after_lock', 'c6b8782eb_pool_usable_after_attack', 'cf9991bbb_nonzero_debt_count_is_zero_at_lock_completion', 'c476d2827_nonzero_debt_count_at_lock_completion'] UNBOUND, compile=-) |
| Forte__Float128_Solidity_Library_evjHaYmvKxh__kAkKE5sSeTR__G9JhCyBVTcC | rebind | revert_expected_test | binding_error | 0 | binding repairable: run stage3_verdict_loop to re-propose (0 UNBOUND, compile=-) |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__vcmNqStwjRg__6bECv5mp6yL | rebind | revert_expected_test | partial_binding | 3 | binding repairable: run stage3_verdict_loop to re-propose (['cd92f3bb5_actual_order_price', 'cd92f3bb5_broken_list_price_discrepancy_possible', 'cd92f3bb5_price_applied_on_match'] UNBOUND, compile=-) |
| Monetrix_L3gNZDymiju__vbdhAfq36PC__NaDr87ezifs | rebind | revert_expected_test | compile_error | 2 | binding repairable: run stage3_verdict_loop to re-propose (['cee91febd_pm_borrow_value', 'cee91febd_pm_supply_value'] UNBOUND, compile=binding_compile_failure) |
| Hybra_Finance_xo4hapwL2Jy__7RVCVStDrsF__gnqEfQdwf7p | rebind | state_assert_test | compile_error | 0 | binding repairable: run stage3_verdict_loop to re-propose (0 UNBOUND, compile=binding_compile_failure) |
| Hybra_Finance_xo4hapwL2Jy__LJk286Uvei7__8Mfy6xJ35eR | rebind | state_assert_test | binding_error | 0 | binding repairable: run stage3_verdict_loop to re-propose (0 UNBOUND, compile=-) |
| Intuition_2VUsxVJwReb__6YNDfbQYkTa__YGqgewwYA9H | rebind | state_assert_test | partial_binding | 4 | binding repairable: run stage3_verdict_loop to re-propose (['c12cc67a0_owner_valid_until', 'cd7c3e247_validity_window_in_signed_digest', 'cd7c3e247_trailing_bytes_mutation_invalidates_recovered_address', 'cd7c3e247_expiry_reliable_for_safety'] UNBOUND, compile=-) |
| Intuition_2VUsxVJwReb__aayBh4TiWVT__JJJgSRQyK2f | rebind | state_assert_test | reference_patch_required | 4 | binding repairable: run stage3_verdict_loop to re-propose (['cea732270_epoch_n_end_timestamp', 'cea732270_epoch_n_plus_1_start_timestamp', 'cea732270_epoch_n_balance_mutation_timestamp', 'cea732270_epoch_n_mutable_at_n_plus_1_start'] UNBOUND, compile=-) |
| Kinetiq_k8aVPPVguSE__Et2e5TnpUga__wHqL6oK9ToF | rebind | state_assert_test | reference_patch_required | 0 | binding repairable: run stage3_verdict_loop to re-propose (0 UNBOUND, compile=-) |
| Olas_j3PRAMM3fVq__xAqoTentyEj__rBebLDJpU3W | rebind | state_assert_test | compile_error | 0 | binding repairable: run stage3_verdict_loop to re-propose (0 UNBOUND, compile=binding_compile_failure) |
| Panoptic__Next_Core_iqcUwAhCZyD__AA46LPa6pbL__dV9PDL3VJ3m | rebind | state_assert_test | compile_error | 0 | binding repairable: run stage3_verdict_loop to re-propose (0 UNBOUND, compile=binding_compile_failure) |
| Panoptic__Next_Core_iqcUwAhCZyD__CUEQdPu878N__ayGYSR98MV8 | rebind | state_assert_test | partial_binding | 2 | binding repairable: run stage3_verdict_loop to re-propose (['init_called_by_factory', 'builder_admin_overwritten'] UNBOUND, compile=-) |
| Panoptic__Next_Core_iqcUwAhCZyD__SXv7e4wnnbo__aSN55Rnh4p8 | rebind | state_assert_test | compile_error | 3 | binding repairable: run stage3_verdict_loop to re-propose (['caa6711e4_guardian_authorized_unlock', 'c52622460_lock_mode_after_rebase', 'c52622460_lock_mode_guardian_set'] UNBOUND, compile=binding_compile_failure) |
| Virtuals_Protocol_hzMS6ZZkBTg__uRCNRZgiUjz__j6HuVHjfaBC | rebind | state_assert_test | partial_binding | 3 | binding repairable: run stage3_verdict_loop to re-propose (['change', 'elo_b_after', 'elo_b_expected_after'] UNBOUND, compile=-) |
| Ekubo_3FTodhsvBkM__TuLiGdJaxpt__2VpY9ZKEXeo | stage2_rerun | no_body | no_summary | 0 | stage-2 product missing or invariant holds vacuously on the exploit path (stage2:no_stage2_run) |
| Merkl_T4ExvutBBXC__V6VRqYmA4BA__MZCDvNevrjd | stage2_rerun | revert_expected_test | violation_not_reproduced | 0 | stage-2 product missing or invariant holds vacuously on the exploit path (invariant_holds_on_exploit_path) |
| Morpheus_kdPtwopH6ws__frkcGbwAqGW__cWxqBprb2Ss | stage2_rerun | revert_expected_test | violation_not_reproduced | 0 | stage-2 product missing or invariant holds vacuously on the exploit path (invariant_holds_on_exploit_path) |
| Virtuals_Protocol_hzMS6ZZkBTg__yc36fBWWe3H__jrMhUzQFvnU | stage2_rerun | state_assert_test | effect_observed_invariant_holds | 0 | stage-2 product missing or invariant holds vacuously on the exploit path (invariant_holds_on_exploit_path) |
| Covenant_d4uY8y2AMSs__otmbJXz4irq__h23uU6Ai3Mx | witness_poc | other_test | binding_error | 0 | original PoC is not Success: repair the test harness first |
| Covenant_d4uY8y2AMSs__CF5ba95T4KR__5atNeQZ3fR4 | witness_poc | revert_expected_test | compile_error | 0 | original PoC is not Success: repair the test harness first |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__FbQktkofz8X__yG32SUkqYGK | witness_poc | state_assert_test | violation_not_reproduced | 0 | original PoC is not Success: repair the test harness first |
| Kinetiq_k8aVPPVguSE__bP38mw3SCq2__eEvYodNRrvz | witness_poc | state_assert_test | preconditions_infeasible_on_code | 0 | original PoC is not Success: repair the test harness first |
| Hybra_Finance_xo4hapwL2Jy__jegipCJB5Kv__dQUWyfXRnAP | retry_inconclusive | other_test | inconclusive | 2 | LLM verdict abstained: retry with repair hint |
| Virtuals_Protocol_hzMS6ZZkBTg__bp8cZknNbnC__eSjbpXjKeUJ | retry_inconclusive | other_test | inconclusive | 0 | LLM verdict abstained: retry with repair hint |
| Hybra_Finance_xo4hapwL2Jy__XgPnfi6S3qh__TJzbsr7Tbkg | retry_inconclusive | revert_expected_test | binding_error | 2 | LLM verdict abstained: retry with repair hint |
| Hybra_Finance_xo4hapwL2Jy__F4rfhrN24eF__f549enU39vL | reference_patch | other_test | not_dynamically_expressible | 1 | multi-contract / unobservable should-be semantics: build an M1 reference patch rather than auto-assert |
| Hybra_Finance_xo4hapwL2Jy__fsfqfuE2eMf__nb9hn2hBQ2b | reference_patch | other_test | binding_error | 0 | multi-contract / unobservable should-be semantics: build an M1 reference patch rather than auto-assert |
| Kinetiq_k8aVPPVguSE__YdUkynebFvW__FCU4bMUR3hY | reference_patch | revert_expected_test | not_dynamically_expressible | 6 | multi-contract / unobservable should-be semantics: build an M1 reference patch rather than auto-assert |
| Intuition_2VUsxVJwReb__aayBh4TiWVT__7YSswxrdK8D | reference_patch | state_assert_test | reference_patch_required | 0 | multi-contract / unobservable should-be semantics: build an M1 reference patch rather than auto-assert |
