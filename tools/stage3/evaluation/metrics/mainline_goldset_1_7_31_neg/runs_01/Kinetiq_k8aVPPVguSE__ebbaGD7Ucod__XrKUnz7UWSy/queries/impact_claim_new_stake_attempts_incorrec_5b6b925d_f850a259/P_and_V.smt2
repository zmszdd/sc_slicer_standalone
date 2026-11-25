; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4ed0e366_actual_remaining_capacity () Int)
(declare-fun c4ed0e366_effective_stake_after_slash () Int)
(declare-fun c4ed0e366_new_stake_attempt_rejected () Bool)
(declare-fun c4ed0e366_slashing_amount () Int)
(declare-fun c4ed0e366_staking_limit () Int)
(declare-fun c4ed0e366_total_staked_before () Int)
(assert
 (= c4ed0e366_actual_remaining_capacity c4ed0e366_actual_remaining_capacity))
(assert
 (= c4ed0e366_effective_stake_after_slash c4ed0e366_effective_stake_after_slash))
(assert
 (= c4ed0e366_new_stake_attempt_rejected c4ed0e366_new_stake_attempt_rejected))
(assert
 (= c4ed0e366_slashing_amount c4ed0e366_slashing_amount))
(assert
 (= c4ed0e366_staking_limit c4ed0e366_staking_limit))
(assert
 (= c4ed0e366_total_staked_before c4ed0e366_total_staked_before))
(define-fun report_preconditions () Bool (and (= 100 c4ed0e366_staking_limit)
     (= 70 c4ed0e366_total_staked_before)
     (= 20 c4ed0e366_slashing_amount)
     (= 50 c4ed0e366_effective_stake_after_slash)))
(define-fun report_safety () Bool (=> (= c4ed0e366_actual_remaining_capacity
       (- c4ed0e366_staking_limit c4ed0e366_effective_stake_after_slash))
    (=> (< 0 c4ed0e366_actual_remaining_capacity)
        (not c4ed0e366_new_stake_attempt_rejected))))
(define-fun report_effects () Bool (and (= c4ed0e366_actual_remaining_capacity
        (- c4ed0e366_staking_limit c4ed0e366_effective_stake_after_slash))
     (< 0 c4ed0e366_actual_remaining_capacity)
     c4ed0e366_new_stake_attempt_rejected
     c4ed0e366_new_stake_attempt_rejected
     (< 0 c4ed0e366_actual_remaining_capacity)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
