; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c630855d2_funds_stolen_from_position_holders () Bool)
(declare-fun c630855d2_itm_position_eligible_exists () Bool)
(declare-fun c630855d2_settlement_uses_manipulable_spot () Bool)
(declare-fun c630855d2_tick_twap_deviation_under_513 () Bool)
(assert
 (= c630855d2_funds_stolen_from_position_holders c630855d2_funds_stolen_from_position_holders))
(assert
 (= c630855d2_itm_position_eligible_exists c630855d2_itm_position_eligible_exists))
(assert
 (= c630855d2_settlement_uses_manipulable_spot c630855d2_settlement_uses_manipulable_spot))
(assert
 (= c630855d2_tick_twap_deviation_under_513 c630855d2_tick_twap_deviation_under_513))
(define-fun report_preconditions () Bool (and c630855d2_itm_position_eligible_exists
     c630855d2_tick_twap_deviation_under_513))
(define-fun report_safety () Bool (=> c630855d2_itm_position_eligible_exists
    (not c630855d2_settlement_uses_manipulable_spot)))
(define-fun report_effects () Bool (and c630855d2_itm_position_eligible_exists
     c630855d2_settlement_uses_manipulable_spot
     c630855d2_funds_stolen_from_position_holders))
