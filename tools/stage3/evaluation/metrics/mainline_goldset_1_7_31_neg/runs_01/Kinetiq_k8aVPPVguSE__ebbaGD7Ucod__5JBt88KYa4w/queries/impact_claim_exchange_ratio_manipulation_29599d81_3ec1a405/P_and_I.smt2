; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c10d7a3ff_actual_hype_below_staking_limit () Bool)
(declare-fun c10d7a3ff_exchange_ratio_basis () Int)
(declare-fun c10d7a3ff_exchange_ratio_manipulated () Bool)
(declare-fun c10d7a3ff_slashed_funds_present () Bool)
(declare-fun c10d7a3ff_staking_limit_basis () Int)
(assert
 (= c10d7a3ff_actual_hype_below_staking_limit c10d7a3ff_actual_hype_below_staking_limit))
(assert
 (= c10d7a3ff_exchange_ratio_basis c10d7a3ff_exchange_ratio_basis))
(assert
 (= c10d7a3ff_exchange_ratio_manipulated c10d7a3ff_exchange_ratio_manipulated))
(assert
 (= c10d7a3ff_slashed_funds_present c10d7a3ff_slashed_funds_present))
(assert
 (= c10d7a3ff_staking_limit_basis c10d7a3ff_staking_limit_basis))
(define-fun report_preconditions () Bool (and c10d7a3ff_slashed_funds_present c10d7a3ff_actual_hype_below_staking_limit))
(define-fun report_safety () Bool (=> c10d7a3ff_slashed_funds_present
    (= c10d7a3ff_staking_limit_basis c10d7a3ff_exchange_ratio_basis)))
(define-fun report_effects () Bool (and c10d7a3ff_slashed_funds_present
     (not (= c10d7a3ff_staking_limit_basis c10d7a3ff_exchange_ratio_basis))
     c10d7a3ff_exchange_ratio_manipulated))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
