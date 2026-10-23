; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c81bc24c7_limit_order_match_in_progress () Bool)
(declare-fun c81bc24c7_limit_order_matching_reverts () Bool)
(declare-fun c81bc24c7_matched_amounts_disjoint_bits () Bool)
(declare-fun c81bc24c7_matched_base_nonzero () Bool)
(declare-fun c81bc24c7_matched_quote_nonzero () Bool)
(declare-fun c81bc24c7_rejected_as_zero_cost_trade () Bool)
(assert
 (= c81bc24c7_limit_order_match_in_progress c81bc24c7_limit_order_match_in_progress))
(assert
 (= c81bc24c7_limit_order_matching_reverts c81bc24c7_limit_order_matching_reverts))
(assert
 (= c81bc24c7_matched_amounts_disjoint_bits c81bc24c7_matched_amounts_disjoint_bits))
(assert
 (= c81bc24c7_matched_base_nonzero c81bc24c7_matched_base_nonzero))
(assert
 (= c81bc24c7_matched_quote_nonzero c81bc24c7_matched_quote_nonzero))
(assert
 (= c81bc24c7_rejected_as_zero_cost_trade c81bc24c7_rejected_as_zero_cost_trade))
(define-fun report_preconditions () Bool (and c81bc24c7_limit_order_match_in_progress
     c81bc24c7_matched_amounts_disjoint_bits))
(define-fun report_safety () Bool (=> (and c81bc24c7_limit_order_match_in_progress
         c81bc24c7_matched_base_nonzero
         c81bc24c7_matched_quote_nonzero)
    (not c81bc24c7_rejected_as_zero_cost_trade)))
(define-fun report_effects () Bool (and c81bc24c7_limit_order_matching_reverts
     c81bc24c7_limit_order_matching_reverts))
(assert report_preconditions)
(check-sat)
(get-model)
