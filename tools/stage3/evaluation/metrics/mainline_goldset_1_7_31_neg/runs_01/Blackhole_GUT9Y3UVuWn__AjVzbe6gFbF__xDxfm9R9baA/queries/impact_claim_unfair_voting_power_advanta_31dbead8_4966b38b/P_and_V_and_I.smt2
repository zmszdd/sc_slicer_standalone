; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc0d2e8e1_conversion_applies_one_time_bonus () Bool)
(declare-fun cc0d2e8e1_conversion_to_smnft_occurs () Bool)
(declare-fun cc0d2e8e1_position_is_previously_bonused () Bool)
(declare-fun cc0d2e8e1_unfair_voting_power_advantage_created () Bool)
(assert
 (= cc0d2e8e1_conversion_applies_one_time_bonus cc0d2e8e1_conversion_applies_one_time_bonus))
(assert
 (= cc0d2e8e1_conversion_to_smnft_occurs cc0d2e8e1_conversion_to_smnft_occurs))
(assert
 (= cc0d2e8e1_position_is_previously_bonused cc0d2e8e1_position_is_previously_bonused))
(assert
 (= cc0d2e8e1_unfair_voting_power_advantage_created cc0d2e8e1_unfair_voting_power_advantage_created))
(define-fun report_preconditions () Bool (and cc0d2e8e1_position_is_previously_bonused
     cc0d2e8e1_conversion_to_smnft_occurs))
(define-fun report_safety () Bool cc0d2e8e1_conversion_applies_one_time_bonus)
(define-fun report_effects () Bool (and cc0d2e8e1_conversion_to_smnft_occurs
     (not cc0d2e8e1_conversion_applies_one_time_bonus)
     cc0d2e8e1_unfair_voting_power_advantage_created))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
