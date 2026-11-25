; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cf2856d48_legitimate_match_nonzero_both_sides () Bool)
(declare-fun cf2856d48_limit_order_match_processing () Bool)
(declare-fun cf2856d48_match_rejected_as_zero_cost () Bool)
(declare-fun cf2856d48_matched_amounts_disjoint_bits () Bool)
(declare-fun cf2856d48_user_experience_damaged () Bool)
(assert
 (= cf2856d48_legitimate_match_nonzero_both_sides cf2856d48_legitimate_match_nonzero_both_sides))
(assert
 (= cf2856d48_limit_order_match_processing cf2856d48_limit_order_match_processing))
(assert
 (= cf2856d48_match_rejected_as_zero_cost cf2856d48_match_rejected_as_zero_cost))
(assert
 (= cf2856d48_matched_amounts_disjoint_bits cf2856d48_matched_amounts_disjoint_bits))
(assert
 (= cf2856d48_user_experience_damaged cf2856d48_user_experience_damaged))
(define-fun report_preconditions () Bool (and cf2856d48_limit_order_match_processing
     cf2856d48_matched_amounts_disjoint_bits))
(define-fun report_safety () Bool (=> (and cf2856d48_limit_order_match_processing
         cf2856d48_legitimate_match_nonzero_both_sides)
    (not cf2856d48_match_rejected_as_zero_cost)))
(define-fun report_effects () Bool (and cf2856d48_limit_order_match_processing
     cf2856d48_legitimate_match_nonzero_both_sides
     cf2856d48_match_rejected_as_zero_cost
     cf2856d48_user_experience_damaged))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
