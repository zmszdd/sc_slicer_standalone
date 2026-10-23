; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd8db3bef_amounts_disjoint_bits () Bool)
(declare-fun cd8db3bef_limit_order_match_in_progress () Bool)
(declare-fun cd8db3bef_limit_order_matching_reverts () Bool)
(declare-fun cd8db3bef_matched_base_is_power_of_two () Bool)
(declare-fun cd8db3bef_matched_quote_less_than_base () Bool)
(assert
 (= cd8db3bef_amounts_disjoint_bits cd8db3bef_amounts_disjoint_bits))
(assert
 (= cd8db3bef_limit_order_match_in_progress cd8db3bef_limit_order_match_in_progress))
(assert
 (= cd8db3bef_limit_order_matching_reverts cd8db3bef_limit_order_matching_reverts))
(assert
 (= cd8db3bef_matched_base_is_power_of_two cd8db3bef_matched_base_is_power_of_two))
(assert
 (= cd8db3bef_matched_quote_less_than_base cd8db3bef_matched_quote_less_than_base))
(define-fun report_preconditions () Bool (and cd8db3bef_limit_order_match_in_progress
     cd8db3bef_matched_base_is_power_of_two
     cd8db3bef_matched_quote_less_than_base
     cd8db3bef_amounts_disjoint_bits))
(define-fun report_safety () Bool (=> (and cd8db3bef_limit_order_match_in_progress
         cd8db3bef_limit_order_matching_reverts)
    (=> (and cd8db3bef_limit_order_match_in_progress
             cd8db3bef_matched_base_is_power_of_two
             cd8db3bef_matched_quote_less_than_base
             cd8db3bef_amounts_disjoint_bits)
        (not cd8db3bef_limit_order_matching_reverts))))
(define-fun report_effects () Bool (and cd8db3bef_limit_order_match_in_progress
     cd8db3bef_limit_order_matching_reverts
     cd8db3bef_limit_order_match_in_progress
     cd8db3bef_matched_base_is_power_of_two
     cd8db3bef_matched_quote_less_than_base
     cd8db3bef_amounts_disjoint_bits
     (not (not cd8db3bef_limit_order_matching_reverts))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
