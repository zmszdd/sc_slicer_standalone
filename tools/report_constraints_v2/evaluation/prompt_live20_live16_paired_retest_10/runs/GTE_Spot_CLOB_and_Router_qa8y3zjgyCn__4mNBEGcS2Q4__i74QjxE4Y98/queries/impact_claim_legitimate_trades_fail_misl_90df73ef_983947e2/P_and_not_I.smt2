; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0f778f54_legitimate_trade_fails_misleading_error () Bool)
(declare-fun c0f778f54_limit_order_match_in_progress () Bool)
(declare-fun c0f778f54_matched_amounts_disjoint_bits () Bool)
(declare-fun c0f778f54_zero_cost_guard_triggered () Bool)
(assert
 (= c0f778f54_legitimate_trade_fails_misleading_error c0f778f54_legitimate_trade_fails_misleading_error))
(assert
 (= c0f778f54_limit_order_match_in_progress c0f778f54_limit_order_match_in_progress))
(assert
 (= c0f778f54_matched_amounts_disjoint_bits c0f778f54_matched_amounts_disjoint_bits))
(assert
 (= c0f778f54_zero_cost_guard_triggered c0f778f54_zero_cost_guard_triggered))
(define-fun report_preconditions () Bool (and c0f778f54_limit_order_match_in_progress
     c0f778f54_matched_amounts_disjoint_bits))
(define-fun report_safety () Bool (=> (and c0f778f54_limit_order_match_in_progress
         c0f778f54_matched_amounts_disjoint_bits)
    (not c0f778f54_zero_cost_guard_triggered)))
(define-fun report_effects () Bool c0f778f54_legitimate_trade_fails_misleading_error)
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
