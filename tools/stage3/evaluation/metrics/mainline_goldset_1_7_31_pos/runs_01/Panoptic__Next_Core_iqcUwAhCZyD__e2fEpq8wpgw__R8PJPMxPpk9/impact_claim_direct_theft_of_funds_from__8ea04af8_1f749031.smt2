; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c5fff977b_funds_stolen_from_holders () Bool)
(declare-fun c5fff977b_holder_receives_fair_value () Bool)
(declare-fun c5fff977b_itm_position_eligible_exists () Bool)
(declare-fun c5fff977b_tick_twap_deviation_ticks () Int)
(assert
 (= c5fff977b_funds_stolen_from_holders c5fff977b_funds_stolen_from_holders))
(assert
 (= c5fff977b_holder_receives_fair_value c5fff977b_holder_receives_fair_value))
(assert
 (= c5fff977b_itm_position_eligible_exists c5fff977b_itm_position_eligible_exists))
(assert
 (= c5fff977b_tick_twap_deviation_ticks c5fff977b_tick_twap_deviation_ticks))
(define-fun report_preconditions () Bool (and c5fff977b_itm_position_eligible_exists
     (> 513 c5fff977b_tick_twap_deviation_ticks)))
(define-fun report_safety () Bool (=> c5fff977b_itm_position_eligible_exists c5fff977b_holder_receives_fair_value))
(define-fun report_effects () Bool (and c5fff977b_itm_position_eligible_exists
     (not c5fff977b_holder_receives_fair_value)
     c5fff977b_funds_stolen_from_holders))
