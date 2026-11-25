; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c65e4bcb2_actual_amount_under_management () Int)
(declare-fun c65e4bcb2_new_stake_rejected () Bool)
(declare-fun c65e4bcb2_staking_limit () Int)
(declare-fun c65e4bcb2_total_slashed_amount () Int)
(assert
 (= c65e4bcb2_actual_amount_under_management c65e4bcb2_actual_amount_under_management))
(assert
 (= c65e4bcb2_new_stake_rejected c65e4bcb2_new_stake_rejected))
(assert
 (= c65e4bcb2_staking_limit c65e4bcb2_staking_limit))
(assert
 (= c65e4bcb2_total_slashed_amount c65e4bcb2_total_slashed_amount))
(define-fun report_preconditions () Bool (and (< 0 c65e4bcb2_staking_limit) (< 0 c65e4bcb2_total_slashed_amount)))
(define-fun report_safety () Bool (=> (< c65e4bcb2_actual_amount_under_management c65e4bcb2_staking_limit)
    (not c65e4bcb2_new_stake_rejected)))
(define-fun report_effects () Bool (and (and (< c65e4bcb2_actual_amount_under_management c65e4bcb2_staking_limit)
          c65e4bcb2_new_stake_rejected)
     c65e4bcb2_new_stake_rejected
     (and (< c65e4bcb2_actual_amount_under_management c65e4bcb2_staking_limit)
          c65e4bcb2_new_stake_rejected)))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
