; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c139784cd_additional_bonus_received () Bool)
(declare-fun c139784cd_bonus_applied_count () Int)
(declare-fun c139784cd_one_time_bonus_limit () Int)
(declare-fun c139784cd_position_is_previously_bonused () Bool)
(assert
 (= c139784cd_additional_bonus_received c139784cd_additional_bonus_received))
(assert
 (= c139784cd_bonus_applied_count c139784cd_bonus_applied_count))
(assert
 (= c139784cd_one_time_bonus_limit c139784cd_one_time_bonus_limit))
(assert
 (= c139784cd_position_is_previously_bonused c139784cd_position_is_previously_bonused))
(define-fun report_preconditions () Bool c139784cd_position_is_previously_bonused)
(define-fun report_safety () Bool (=> c139784cd_position_is_previously_bonused
    (<= c139784cd_bonus_applied_count c139784cd_one_time_bonus_limit)))
(define-fun report_effects () Bool (and c139784cd_position_is_previously_bonused
     (not (<= c139784cd_bonus_applied_count c139784cd_one_time_bonus_limit))
     c139784cd_additional_bonus_received))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
