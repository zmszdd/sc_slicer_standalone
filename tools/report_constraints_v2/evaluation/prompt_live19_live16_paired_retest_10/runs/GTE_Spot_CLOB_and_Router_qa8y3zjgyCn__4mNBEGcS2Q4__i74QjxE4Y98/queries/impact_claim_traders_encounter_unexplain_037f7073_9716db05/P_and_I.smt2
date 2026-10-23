; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1c2382ad_base_amount_nonzero () Bool)
(declare-fun c1c2382ad_limit_order_match_in_progress () Bool)
(declare-fun c1c2382ad_matched_amounts_disjoint_bits_hold () Bool)
(declare-fun c1c2382ad_quote_amount_nonzero () Bool)
(declare-fun c1c2382ad_reverts_with_zero_cost_trade () Bool)
(declare-fun c1c2382ad_traders_encounter_unexplained_failures_occurred () Bool)
(assert
 (= c1c2382ad_base_amount_nonzero c1c2382ad_base_amount_nonzero))
(assert
 (= c1c2382ad_limit_order_match_in_progress c1c2382ad_limit_order_match_in_progress))
(assert
 (= c1c2382ad_matched_amounts_disjoint_bits_hold c1c2382ad_matched_amounts_disjoint_bits_hold))
(assert
 (= c1c2382ad_quote_amount_nonzero c1c2382ad_quote_amount_nonzero))
(assert
 (= c1c2382ad_reverts_with_zero_cost_trade c1c2382ad_reverts_with_zero_cost_trade))
(assert
 (= c1c2382ad_traders_encounter_unexplained_failures_occurred c1c2382ad_traders_encounter_unexplained_failures_occurred))
(define-fun report_preconditions () Bool (and c1c2382ad_limit_order_match_in_progress
     c1c2382ad_matched_amounts_disjoint_bits_hold))
(define-fun report_safety () Bool (=> c1c2382ad_traders_encounter_unexplained_failures_occurred
    (=> (and c1c2382ad_limit_order_match_in_progress
             c1c2382ad_base_amount_nonzero
             c1c2382ad_quote_amount_nonzero)
        (not c1c2382ad_reverts_with_zero_cost_trade))))
(define-fun report_effects () Bool (and c1c2382ad_traders_encounter_unexplained_failures_occurred
     c1c2382ad_limit_order_match_in_progress
     c1c2382ad_base_amount_nonzero
     c1c2382ad_quote_amount_nonzero
     (not (not c1c2382ad_reverts_with_zero_cost_trade))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
