; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd8db3bef_limit_order_match_in_progress () Bool)
(declare-fun cd8db3bef_limit_order_matching_reverts () Bool)
(declare-fun cd8db3bef_matched_amounts_disjoint_bits_hold () Bool)
(declare-fun cd8db3bef_zero_cost_guard_rejects_only_zero_cost () Bool)
(assert
 (= cd8db3bef_limit_order_match_in_progress cd8db3bef_limit_order_match_in_progress))
(assert
 (= cd8db3bef_limit_order_matching_reverts cd8db3bef_limit_order_matching_reverts))
(assert
 (= cd8db3bef_matched_amounts_disjoint_bits_hold cd8db3bef_matched_amounts_disjoint_bits_hold))
(assert
 (= cd8db3bef_zero_cost_guard_rejects_only_zero_cost cd8db3bef_zero_cost_guard_rejects_only_zero_cost))
(define-fun report_preconditions () Bool (and cd8db3bef_limit_order_match_in_progress
     cd8db3bef_matched_amounts_disjoint_bits_hold))
(define-fun report_safety () Bool (=> (and cd8db3bef_limit_order_match_in_progress
         cd8db3bef_limit_order_matching_reverts)
    (=> (and cd8db3bef_limit_order_match_in_progress
             cd8db3bef_matched_amounts_disjoint_bits_hold
             cd8db3bef_zero_cost_guard_rejects_only_zero_cost)
        (not cd8db3bef_limit_order_matching_reverts))))
(define-fun report_effects () Bool (and cd8db3bef_limit_order_match_in_progress
     cd8db3bef_limit_order_matching_reverts
     cd8db3bef_limit_order_match_in_progress
     cd8db3bef_matched_amounts_disjoint_bits_hold
     cd8db3bef_zero_cost_guard_rejects_only_zero_cost
     (not (not cd8db3bef_limit_order_matching_reverts))))
(assert report_preconditions)
(check-sat)
(get-model)
