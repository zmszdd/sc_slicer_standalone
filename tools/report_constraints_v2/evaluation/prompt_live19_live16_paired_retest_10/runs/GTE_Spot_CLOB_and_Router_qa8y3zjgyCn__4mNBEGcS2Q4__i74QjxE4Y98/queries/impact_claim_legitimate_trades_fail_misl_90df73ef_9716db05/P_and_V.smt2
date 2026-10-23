; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c878a3737_limit_order_match_in_progress () Bool)
(declare-fun c878a3737_matched_amounts_bitwise_disjoint () Bool)
(declare-fun c878a3737_zero_cost_trade_revert_occurred () Bool)
(assert
 (= c878a3737_limit_order_match_in_progress c878a3737_limit_order_match_in_progress))
(assert
 (= c878a3737_matched_amounts_bitwise_disjoint c878a3737_matched_amounts_bitwise_disjoint))
(assert
 (= c878a3737_zero_cost_trade_revert_occurred c878a3737_zero_cost_trade_revert_occurred))
(define-fun report_preconditions () Bool (and c878a3737_limit_order_match_in_progress
     c878a3737_matched_amounts_bitwise_disjoint))
(define-fun report_safety () Bool (=> c878a3737_zero_cost_trade_revert_occurred
    (=> (and c878a3737_limit_order_match_in_progress
             c878a3737_matched_amounts_bitwise_disjoint)
        (not c878a3737_zero_cost_trade_revert_occurred))))
(define-fun report_effects () Bool (and c878a3737_zero_cost_trade_revert_occurred
     c878a3737_limit_order_match_in_progress
     c878a3737_matched_amounts_bitwise_disjoint
     (not (not c878a3737_zero_cost_trade_revert_occurred))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
