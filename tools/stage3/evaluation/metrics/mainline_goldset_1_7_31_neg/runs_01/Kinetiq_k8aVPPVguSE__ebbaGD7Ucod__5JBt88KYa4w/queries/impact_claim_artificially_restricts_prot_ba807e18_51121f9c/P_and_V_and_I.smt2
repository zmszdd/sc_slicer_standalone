; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc80895a6_actual_hype_in_system () Int)
(declare-fun cc80895a6_capacity_artificially_restricted () Bool)
(declare-fun cc80895a6_new_stake_submitted () Bool)
(declare-fun cc80895a6_slashed_funds_present () Bool)
(declare-fun cc80895a6_staking_limit () Int)
(assert
 (= cc80895a6_actual_hype_in_system cc80895a6_actual_hype_in_system))
(assert
 (= cc80895a6_capacity_artificially_restricted cc80895a6_capacity_artificially_restricted))
(assert
 (= cc80895a6_new_stake_submitted cc80895a6_new_stake_submitted))
(assert
 (= cc80895a6_slashed_funds_present cc80895a6_slashed_funds_present))
(assert
 (= cc80895a6_staking_limit cc80895a6_staking_limit))
(define-fun report_preconditions () Bool (and cc80895a6_slashed_funds_present cc80895a6_new_stake_submitted))
(define-fun report_safety () Bool (=> cc80895a6_new_stake_submitted
    (<= cc80895a6_actual_hype_in_system cc80895a6_staking_limit)))
(define-fun report_effects () Bool (and cc80895a6_new_stake_submitted
     (not (<= cc80895a6_actual_hype_in_system cc80895a6_staking_limit))
     cc80895a6_capacity_artificially_restricted))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
