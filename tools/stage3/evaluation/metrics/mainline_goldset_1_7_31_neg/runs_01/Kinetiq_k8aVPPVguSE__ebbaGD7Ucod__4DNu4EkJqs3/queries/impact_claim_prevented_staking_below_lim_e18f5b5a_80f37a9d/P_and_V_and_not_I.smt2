; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c33298abf_actual_staked_after_slashing () Int)
(declare-fun c33298abf_capacity_reflects_actual_staked () Bool)
(declare-fun c33298abf_rewards_amount_before () Int)
(declare-fun c33298abf_slashed_amount () Int)
(declare-fun c33298abf_staking_limit () Int)
(declare-fun c33298abf_staking_prevented_below_limit () Bool)
(declare-fun c33298abf_total_claimed_before () Int)
(declare-fun c33298abf_total_staked_before () Int)
(assert
 (= c33298abf_actual_staked_after_slashing c33298abf_actual_staked_after_slashing))
(assert
 (= c33298abf_capacity_reflects_actual_staked c33298abf_capacity_reflects_actual_staked))
(assert
 (= c33298abf_rewards_amount_before c33298abf_rewards_amount_before))
(assert
 (= c33298abf_slashed_amount c33298abf_slashed_amount))
(assert
 (= c33298abf_staking_limit c33298abf_staking_limit))
(assert
 (= c33298abf_staking_prevented_below_limit c33298abf_staking_prevented_below_limit))
(assert
 (= c33298abf_total_claimed_before c33298abf_total_claimed_before))
(assert
 (= c33298abf_total_staked_before c33298abf_total_staked_before))
(define-fun report_preconditions () Bool (and (= 1000 c33298abf_staking_limit)
     (= 800 c33298abf_total_staked_before)
     (= 100 c33298abf_rewards_amount_before)
     (= 0 c33298abf_total_claimed_before)
     (= 200 c33298abf_slashed_amount)
     (= 600 c33298abf_actual_staked_after_slashing)))
(define-fun report_safety () Bool (=> (< c33298abf_actual_staked_after_slashing c33298abf_staking_limit)
    c33298abf_capacity_reflects_actual_staked))
(define-fun report_effects () Bool (and (< c33298abf_actual_staked_after_slashing c33298abf_staking_limit)
     (not c33298abf_capacity_reflects_actual_staked)
     c33298abf_staking_prevented_below_limit
     (< c33298abf_actual_staked_after_slashing c33298abf_staking_limit)
     c33298abf_staking_prevented_below_limit))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
