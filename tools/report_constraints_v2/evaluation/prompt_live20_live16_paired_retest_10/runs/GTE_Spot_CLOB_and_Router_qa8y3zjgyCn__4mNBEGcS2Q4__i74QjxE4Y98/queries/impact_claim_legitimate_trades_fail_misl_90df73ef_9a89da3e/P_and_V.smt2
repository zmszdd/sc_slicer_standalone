; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8890776b_legitimate_trade_failed_misleading_error () Bool)
(declare-fun c8890776b_limit_order_match_in_progress () Bool)
(declare-fun c8890776b_matched_amounts_bitwise_and () Int)
(declare-fun c8890776b_matched_base_amount () Int)
(declare-fun c8890776b_matched_quote_amount () Int)
(declare-fun c8890776b_zero_cost_rejection_occurred () Bool)
(assert
 (= c8890776b_legitimate_trade_failed_misleading_error c8890776b_legitimate_trade_failed_misleading_error))
(assert
 (= c8890776b_limit_order_match_in_progress c8890776b_limit_order_match_in_progress))
(assert
 (= c8890776b_matched_amounts_bitwise_and c8890776b_matched_amounts_bitwise_and))
(assert
 (= c8890776b_matched_base_amount c8890776b_matched_base_amount))
(assert
 (= c8890776b_matched_quote_amount c8890776b_matched_quote_amount))
(assert
 (= c8890776b_zero_cost_rejection_occurred c8890776b_zero_cost_rejection_occurred))
(define-fun report_preconditions () Bool (and c8890776b_limit_order_match_in_progress
     (= 0 c8890776b_matched_amounts_bitwise_and)))
(define-fun report_safety () Bool (=> (and c8890776b_limit_order_match_in_progress
         (distinct 0 c8890776b_matched_base_amount)
         (distinct 0 c8890776b_matched_quote_amount))
    (not c8890776b_zero_cost_rejection_occurred)))
(define-fun report_effects () Bool c8890776b_legitimate_trade_failed_misleading_error)
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
