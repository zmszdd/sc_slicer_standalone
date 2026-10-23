; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c80326eb2_legitimate_trade_rejected_with_misleading_error () Bool)
(declare-fun c80326eb2_limit_order_match_in_progress () Bool)
(declare-fun c80326eb2_matched_amounts_disjoint_bits_hold () Bool)
(assert
 (= c80326eb2_legitimate_trade_rejected_with_misleading_error c80326eb2_legitimate_trade_rejected_with_misleading_error))
(assert
 (= c80326eb2_limit_order_match_in_progress c80326eb2_limit_order_match_in_progress))
(assert
 (= c80326eb2_matched_amounts_disjoint_bits_hold c80326eb2_matched_amounts_disjoint_bits_hold))
(define-fun report_preconditions () Bool (and c80326eb2_limit_order_match_in_progress
     c80326eb2_matched_amounts_disjoint_bits_hold))
(define-fun report_safety () Bool (=> c80326eb2_legitimate_trade_rejected_with_misleading_error
    (=> (and c80326eb2_limit_order_match_in_progress
             c80326eb2_matched_amounts_disjoint_bits_hold)
        (not c80326eb2_legitimate_trade_rejected_with_misleading_error))))
(define-fun report_effects () Bool (and c80326eb2_legitimate_trade_rejected_with_misleading_error
     c80326eb2_limit_order_match_in_progress
     c80326eb2_matched_amounts_disjoint_bits_hold
     (not (not c80326eb2_legitimate_trade_rejected_with_misleading_error))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
