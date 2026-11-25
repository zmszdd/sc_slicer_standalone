; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1e09a2bc_conversion_applies_one_time_bonus () Bool)
(declare-fun c1e09a2bc_disproportionate_voting_power_gained () Bool)
(declare-fun c1e09a2bc_position_is_previously_bonused () Bool)
(assert
 (= c1e09a2bc_conversion_applies_one_time_bonus c1e09a2bc_conversion_applies_one_time_bonus))
(assert
 (= c1e09a2bc_disproportionate_voting_power_gained c1e09a2bc_disproportionate_voting_power_gained))
(assert
 (= c1e09a2bc_position_is_previously_bonused c1e09a2bc_position_is_previously_bonused))
(define-fun report_preconditions () Bool c1e09a2bc_position_is_previously_bonused)
(define-fun report_safety () Bool (=> c1e09a2bc_position_is_previously_bonused
    c1e09a2bc_conversion_applies_one_time_bonus))
(define-fun report_effects () Bool (and c1e09a2bc_position_is_previously_bonused
     (not c1e09a2bc_conversion_applies_one_time_bonus)
     c1e09a2bc_disproportionate_voting_power_gained))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
