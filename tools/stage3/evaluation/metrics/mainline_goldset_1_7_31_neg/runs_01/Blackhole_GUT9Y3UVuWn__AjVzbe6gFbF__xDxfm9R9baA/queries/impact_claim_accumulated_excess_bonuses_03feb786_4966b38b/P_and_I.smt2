; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c57bb965e_conversion_applies_one_time_bonus () Bool)
(declare-fun c57bb965e_multiple_conversions_accumulate_excess_bonuses () Bool)
(declare-fun c57bb965e_position_is_previously_bonused () Bool)
(assert
 (= c57bb965e_conversion_applies_one_time_bonus c57bb965e_conversion_applies_one_time_bonus))
(assert
 (= c57bb965e_multiple_conversions_accumulate_excess_bonuses c57bb965e_multiple_conversions_accumulate_excess_bonuses))
(assert
 (= c57bb965e_position_is_previously_bonused c57bb965e_position_is_previously_bonused))
(define-fun report_preconditions () Bool c57bb965e_position_is_previously_bonused)
(define-fun report_safety () Bool (=> c57bb965e_position_is_previously_bonused
    c57bb965e_conversion_applies_one_time_bonus))
(define-fun report_effects () Bool (and c57bb965e_position_is_previously_bonused
     (not c57bb965e_conversion_applies_one_time_bonus)
     c57bb965e_multiple_conversions_accumulate_excess_bonuses))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
