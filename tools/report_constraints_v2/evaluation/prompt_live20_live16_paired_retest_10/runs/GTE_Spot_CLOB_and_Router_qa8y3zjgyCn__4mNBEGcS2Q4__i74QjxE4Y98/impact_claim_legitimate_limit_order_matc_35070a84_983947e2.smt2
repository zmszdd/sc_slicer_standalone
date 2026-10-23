; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2d9a3fdd_limit_order_match_in_progress () Bool)
(declare-fun c2d9a3fdd_limit_order_matching_reverts () Bool)
(declare-fun c2d9a3fdd_matched_amounts_disjoint_bits () Bool)
(declare-fun c2d9a3fdd_one_side_receives_without_sending () Bool)
(declare-fun c2d9a3fdd_zero_cost_guard_triggered () Bool)
(assert
 (= c2d9a3fdd_limit_order_match_in_progress c2d9a3fdd_limit_order_match_in_progress))
(assert
 (= c2d9a3fdd_limit_order_matching_reverts c2d9a3fdd_limit_order_matching_reverts))
(assert
 (= c2d9a3fdd_matched_amounts_disjoint_bits c2d9a3fdd_matched_amounts_disjoint_bits))
(assert
 (= c2d9a3fdd_one_side_receives_without_sending c2d9a3fdd_one_side_receives_without_sending))
(assert
 (= c2d9a3fdd_zero_cost_guard_triggered c2d9a3fdd_zero_cost_guard_triggered))
(define-fun report_preconditions () Bool (and c2d9a3fdd_limit_order_match_in_progress
     c2d9a3fdd_matched_amounts_disjoint_bits))
(define-fun report_safety () Bool (=> c2d9a3fdd_limit_order_match_in_progress
    (or c2d9a3fdd_one_side_receives_without_sending
        (not c2d9a3fdd_zero_cost_guard_triggered))))
(define-fun report_effects () Bool (and c2d9a3fdd_limit_order_matching_reverts
     c2d9a3fdd_limit_order_match_in_progress))
