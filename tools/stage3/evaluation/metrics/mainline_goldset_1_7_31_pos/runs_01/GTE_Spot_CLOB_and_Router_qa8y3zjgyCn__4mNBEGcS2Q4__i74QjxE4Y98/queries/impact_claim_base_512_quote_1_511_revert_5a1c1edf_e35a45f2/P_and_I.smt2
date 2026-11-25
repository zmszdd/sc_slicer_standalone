; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbcdaf90d_base_is_power_of_two () Bool)
(declare-fun cbcdaf90d_impact_base_amount_512 () Int)
(declare-fun cbcdaf90d_impact_quote_amount () Int)
(declare-fun cbcdaf90d_impact_revert_occurred () Bool)
(declare-fun cbcdaf90d_legitimate_match_nonzero_both_sides () Bool)
(declare-fun cbcdaf90d_match_rejected_as_zero_cost () Bool)
(declare-fun cbcdaf90d_quote_less_than_base () Bool)
(assert
 (= cbcdaf90d_base_is_power_of_two cbcdaf90d_base_is_power_of_two))
(assert
 (= cbcdaf90d_impact_base_amount_512 cbcdaf90d_impact_base_amount_512))
(assert
 (= cbcdaf90d_impact_quote_amount cbcdaf90d_impact_quote_amount))
(assert
 (= cbcdaf90d_impact_revert_occurred cbcdaf90d_impact_revert_occurred))
(assert
 (= cbcdaf90d_legitimate_match_nonzero_both_sides cbcdaf90d_legitimate_match_nonzero_both_sides))
(assert
 (= cbcdaf90d_match_rejected_as_zero_cost cbcdaf90d_match_rejected_as_zero_cost))
(assert
 (= cbcdaf90d_quote_less_than_base cbcdaf90d_quote_less_than_base))
(define-fun report_preconditions () Bool (and cbcdaf90d_base_is_power_of_two
     cbcdaf90d_quote_less_than_base
     cbcdaf90d_legitimate_match_nonzero_both_sides))
(define-fun report_safety () Bool (not cbcdaf90d_match_rejected_as_zero_cost))
(define-fun report_effects () Bool (and cbcdaf90d_legitimate_match_nonzero_both_sides
     cbcdaf90d_match_rejected_as_zero_cost
     (= 512 cbcdaf90d_impact_base_amount_512)
     (<= 1 cbcdaf90d_impact_quote_amount)
     (>= 511 cbcdaf90d_impact_quote_amount)
     cbcdaf90d_impact_revert_occurred
     (= 512 cbcdaf90d_impact_base_amount_512)
     (<= 1 cbcdaf90d_impact_quote_amount)
     (>= 511 cbcdaf90d_impact_quote_amount)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
