; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7a515078_all_limit_order_matching_affected () Bool)
(declare-fun c7a515078_limit_order_match_processing () Bool)
(declare-fun c7a515078_matched_amounts_disjoint_bits () Bool)
(declare-fun c7a515078_matched_base_amount_nonzero () Bool)
(declare-fun c7a515078_matched_quote_amount_nonzero () Bool)
(declare-fun c7a515078_rejected_as_zero_cost_trade () Bool)
(assert
 (= c7a515078_all_limit_order_matching_affected c7a515078_all_limit_order_matching_affected))
(assert
 (= c7a515078_limit_order_match_processing c7a515078_limit_order_match_processing))
(assert
 (= c7a515078_matched_amounts_disjoint_bits c7a515078_matched_amounts_disjoint_bits))
(assert
 (= c7a515078_matched_base_amount_nonzero c7a515078_matched_base_amount_nonzero))
(assert
 (= c7a515078_matched_quote_amount_nonzero c7a515078_matched_quote_amount_nonzero))
(assert
 (= c7a515078_rejected_as_zero_cost_trade c7a515078_rejected_as_zero_cost_trade))
(define-fun report_preconditions () Bool (and c7a515078_limit_order_match_processing
     c7a515078_matched_amounts_disjoint_bits))
(define-fun report_safety () Bool (=> (and c7a515078_limit_order_match_processing
         c7a515078_matched_base_amount_nonzero
         c7a515078_matched_quote_amount_nonzero)
    (not c7a515078_rejected_as_zero_cost_trade)))
(define-fun report_effects () Bool (and c7a515078_limit_order_match_processing
     c7a515078_matched_base_amount_nonzero
     c7a515078_matched_quote_amount_nonzero
     c7a515078_rejected_as_zero_cost_trade
     c7a515078_all_limit_order_matching_affected
     c7a515078_all_limit_order_matching_affected))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
