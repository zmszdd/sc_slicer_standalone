; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd0bfec6c_legitimate_match_nonzero_both_sides () Bool)
(declare-fun cd0bfec6c_limit_order_match_processing () Bool)
(declare-fun cd0bfec6c_matched_amounts_disjoint_bits () Bool)
(declare-fun cd0bfec6c_rejected_as_zero_cost_trade () Bool)
(declare-fun cd0bfec6c_traders_encounter_unexplained_failures () Bool)
(assert
 (= cd0bfec6c_legitimate_match_nonzero_both_sides cd0bfec6c_legitimate_match_nonzero_both_sides))
(assert
 (= cd0bfec6c_limit_order_match_processing cd0bfec6c_limit_order_match_processing))
(assert
 (= cd0bfec6c_matched_amounts_disjoint_bits cd0bfec6c_matched_amounts_disjoint_bits))
(assert
 (= cd0bfec6c_rejected_as_zero_cost_trade cd0bfec6c_rejected_as_zero_cost_trade))
(assert
 (= cd0bfec6c_traders_encounter_unexplained_failures cd0bfec6c_traders_encounter_unexplained_failures))
(define-fun report_preconditions () Bool (and cd0bfec6c_limit_order_match_processing
     cd0bfec6c_matched_amounts_disjoint_bits))
(define-fun report_safety () Bool (=> (and cd0bfec6c_limit_order_match_processing
         cd0bfec6c_legitimate_match_nonzero_both_sides)
    (not cd0bfec6c_rejected_as_zero_cost_trade)))
(define-fun report_effects () Bool (and cd0bfec6c_limit_order_match_processing
     cd0bfec6c_legitimate_match_nonzero_both_sides
     cd0bfec6c_rejected_as_zero_cost_trade
     cd0bfec6c_traders_encounter_unexplained_failures))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
