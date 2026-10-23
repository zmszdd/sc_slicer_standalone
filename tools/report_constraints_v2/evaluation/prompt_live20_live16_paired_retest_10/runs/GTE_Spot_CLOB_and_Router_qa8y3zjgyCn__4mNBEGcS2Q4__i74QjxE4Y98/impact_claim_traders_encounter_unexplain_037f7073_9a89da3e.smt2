; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cf81b6a89_limit_order_match_in_progress () Bool)
(declare-fun cf81b6a89_matched_amounts_disjoint_bits () Bool)
(declare-fun cf81b6a89_matched_base_amount_nonzero () Bool)
(declare-fun cf81b6a89_matched_quote_amount_nonzero () Bool)
(declare-fun cf81b6a89_rejected_as_zero_cost_trade () Bool)
(declare-fun cf81b6a89_traders_encounter_unexplained_failures () Bool)
(assert
 (= cf81b6a89_limit_order_match_in_progress cf81b6a89_limit_order_match_in_progress))
(assert
 (= cf81b6a89_matched_amounts_disjoint_bits cf81b6a89_matched_amounts_disjoint_bits))
(assert
 (= cf81b6a89_matched_base_amount_nonzero cf81b6a89_matched_base_amount_nonzero))
(assert
 (= cf81b6a89_matched_quote_amount_nonzero cf81b6a89_matched_quote_amount_nonzero))
(assert
 (= cf81b6a89_rejected_as_zero_cost_trade cf81b6a89_rejected_as_zero_cost_trade))
(assert
 (= cf81b6a89_traders_encounter_unexplained_failures cf81b6a89_traders_encounter_unexplained_failures))
(define-fun report_preconditions () Bool (and cf81b6a89_limit_order_match_in_progress
     cf81b6a89_matched_amounts_disjoint_bits))
(define-fun report_safety () Bool (=> (and cf81b6a89_limit_order_match_in_progress
         cf81b6a89_matched_base_amount_nonzero
         cf81b6a89_matched_quote_amount_nonzero)
    (not cf81b6a89_rejected_as_zero_cost_trade)))
(define-fun report_effects () Bool cf81b6a89_traders_encounter_unexplained_failures)
