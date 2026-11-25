; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c21e9e117_exchange_ratio_manipulated () Bool)
(declare-fun c21e9e117_exchange_ratio_treats_slashed () Bool)
(declare-fun c21e9e117_slashed_funds_present () Bool)
(declare-fun c21e9e117_staking_limit_treats_slashed () Bool)
(assert
 (= c21e9e117_exchange_ratio_manipulated c21e9e117_exchange_ratio_manipulated))
(assert
 (= c21e9e117_exchange_ratio_treats_slashed c21e9e117_exchange_ratio_treats_slashed))
(assert
 (= c21e9e117_slashed_funds_present c21e9e117_slashed_funds_present))
(assert
 (= c21e9e117_staking_limit_treats_slashed c21e9e117_staking_limit_treats_slashed))
(define-fun report_preconditions () Bool c21e9e117_slashed_funds_present)
(define-fun report_safety () Bool (=> c21e9e117_slashed_funds_present
    (= c21e9e117_staking_limit_treats_slashed
       c21e9e117_exchange_ratio_treats_slashed)))
(define-fun report_effects () Bool (and c21e9e117_slashed_funds_present
     (not (= c21e9e117_staking_limit_treats_slashed
             c21e9e117_exchange_ratio_treats_slashed))
     c21e9e117_exchange_ratio_manipulated))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
