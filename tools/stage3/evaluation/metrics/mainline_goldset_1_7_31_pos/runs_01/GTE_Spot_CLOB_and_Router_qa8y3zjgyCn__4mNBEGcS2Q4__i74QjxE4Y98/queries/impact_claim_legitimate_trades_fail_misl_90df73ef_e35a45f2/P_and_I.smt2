; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c218b08b3_both_amounts_nonzero () Bool)
(declare-fun c218b08b3_legitimate_trade_fails_misleading_error () Bool)
(declare-fun c218b08b3_limit_order_match_processing () Bool)
(declare-fun c218b08b3_match_rejected_as_zero_cost () Bool)
(declare-fun c218b08b3_matched_amounts_disjoint_bits () Bool)
(assert
 (= c218b08b3_both_amounts_nonzero c218b08b3_both_amounts_nonzero))
(assert
 (= c218b08b3_legitimate_trade_fails_misleading_error c218b08b3_legitimate_trade_fails_misleading_error))
(assert
 (= c218b08b3_limit_order_match_processing c218b08b3_limit_order_match_processing))
(assert
 (= c218b08b3_match_rejected_as_zero_cost c218b08b3_match_rejected_as_zero_cost))
(assert
 (= c218b08b3_matched_amounts_disjoint_bits c218b08b3_matched_amounts_disjoint_bits))
(define-fun report_preconditions () Bool (and c218b08b3_limit_order_match_processing
     c218b08b3_matched_amounts_disjoint_bits))
(define-fun report_safety () Bool (=> (and c218b08b3_limit_order_match_processing c218b08b3_both_amounts_nonzero)
    (not c218b08b3_match_rejected_as_zero_cost)))
(define-fun report_effects () Bool (and c218b08b3_limit_order_match_processing
     c218b08b3_both_amounts_nonzero
     c218b08b3_match_rejected_as_zero_cost
     c218b08b3_legitimate_trade_fails_misleading_error))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
