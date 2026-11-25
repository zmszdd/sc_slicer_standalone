; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c87caf993_legitimate_match_nonzero_both_sides () Bool)
(declare-fun c87caf993_limit_order_match_processing () Bool)
(declare-fun c87caf993_market_efficiency_damaged () Bool)
(declare-fun c87caf993_match_rejected_as_zero_cost () Bool)
(declare-fun c87caf993_matched_amounts_disjoint_bits () Bool)
(assert
 (= c87caf993_legitimate_match_nonzero_both_sides c87caf993_legitimate_match_nonzero_both_sides))
(assert
 (= c87caf993_limit_order_match_processing c87caf993_limit_order_match_processing))
(assert
 (= c87caf993_market_efficiency_damaged c87caf993_market_efficiency_damaged))
(assert
 (= c87caf993_match_rejected_as_zero_cost c87caf993_match_rejected_as_zero_cost))
(assert
 (= c87caf993_matched_amounts_disjoint_bits c87caf993_matched_amounts_disjoint_bits))
(define-fun report_preconditions () Bool (and c87caf993_limit_order_match_processing
     c87caf993_matched_amounts_disjoint_bits))
(define-fun report_safety () Bool (=> (and c87caf993_limit_order_match_processing
         c87caf993_legitimate_match_nonzero_both_sides)
    (not c87caf993_match_rejected_as_zero_cost)))
(define-fun report_effects () Bool (and c87caf993_limit_order_match_processing
     c87caf993_legitimate_match_nonzero_both_sides
     c87caf993_match_rejected_as_zero_cost
     c87caf993_market_efficiency_damaged))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
