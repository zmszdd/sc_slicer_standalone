; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6759e080_effective_stake_after () Int)
(declare-fun c6759e080_net_staked_used_in_check () Int)
(declare-fun c6759e080_new_stake_rejected () Bool)
(declare-fun c6759e080_slashing_amount () Int)
(declare-fun c6759e080_staking_limit () Int)
(declare-fun c6759e080_total_staked_before () Int)
(assert
 (= c6759e080_effective_stake_after c6759e080_effective_stake_after))
(assert
 (= c6759e080_net_staked_used_in_check c6759e080_net_staked_used_in_check))
(assert
 (= c6759e080_new_stake_rejected c6759e080_new_stake_rejected))
(assert
 (= c6759e080_slashing_amount c6759e080_slashing_amount))
(assert
 (= c6759e080_staking_limit c6759e080_staking_limit))
(assert
 (= c6759e080_total_staked_before c6759e080_total_staked_before))
(define-fun report_preconditions () Bool (and (= 100 c6759e080_staking_limit)
     (= 70 c6759e080_total_staked_before)
     (= 20 c6759e080_slashing_amount)
     (= 50 c6759e080_effective_stake_after)
     c6759e080_new_stake_rejected))
(define-fun report_safety () Bool (=> (= c6759e080_effective_stake_after
       (- c6759e080_total_staked_before c6759e080_slashing_amount))
    (= c6759e080_net_staked_used_in_check c6759e080_effective_stake_after)))
(define-fun report_effects () Bool (and (= c6759e080_effective_stake_after
        (- c6759e080_total_staked_before c6759e080_slashing_amount))
     c6759e080_new_stake_rejected
     (not (= c6759e080_net_staked_used_in_check c6759e080_effective_stake_after))
     c6759e080_new_stake_rejected
     (< c6759e080_effective_stake_after c6759e080_staking_limit)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
