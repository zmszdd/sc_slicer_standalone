; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbbaefd47_limit_order_match_in_progress () Bool)
(declare-fun cbbaefd47_matched_amounts_bitwise_and () Int)
(declare-fun cbbaefd47_zero_cost_trade_reverted () Bool)
(assert
 (= cbbaefd47_limit_order_match_in_progress cbbaefd47_limit_order_match_in_progress))
(assert
 (= cbbaefd47_matched_amounts_bitwise_and cbbaefd47_matched_amounts_bitwise_and))
(assert
 (= cbbaefd47_zero_cost_trade_reverted cbbaefd47_zero_cost_trade_reverted))
(define-fun report_preconditions () Bool (and cbbaefd47_limit_order_match_in_progress
     (= 0 cbbaefd47_matched_amounts_bitwise_and)))
(define-fun report_safety () Bool (=> cbbaefd47_limit_order_match_in_progress
    (=> (and cbbaefd47_limit_order_match_in_progress
             (= 0 cbbaefd47_matched_amounts_bitwise_and))
        (not cbbaefd47_zero_cost_trade_reverted))))
(define-fun report_effects () Bool (and cbbaefd47_limit_order_match_in_progress
     cbbaefd47_limit_order_match_in_progress
     (= 0 cbbaefd47_matched_amounts_bitwise_and)
     (not (not cbbaefd47_zero_cost_trade_reverted))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
