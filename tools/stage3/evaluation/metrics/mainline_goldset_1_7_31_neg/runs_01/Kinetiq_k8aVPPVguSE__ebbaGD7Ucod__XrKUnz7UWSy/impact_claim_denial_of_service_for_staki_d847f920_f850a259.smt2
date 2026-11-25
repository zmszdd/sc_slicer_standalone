; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c60b0665a_effective_stake_hype () Int)
(declare-fun c60b0665a_remaining_capacity_hype () Int)
(declare-fun c60b0665a_slashing_amount_hype () Int)
(declare-fun c60b0665a_stake_attempt_rejected () Bool)
(declare-fun c60b0665a_staking_limit_hype () Int)
(declare-fun c60b0665a_total_staked_before_hype () Int)
(assert
 (= c60b0665a_effective_stake_hype c60b0665a_effective_stake_hype))
(assert
 (= c60b0665a_remaining_capacity_hype c60b0665a_remaining_capacity_hype))
(assert
 (= c60b0665a_slashing_amount_hype c60b0665a_slashing_amount_hype))
(assert
 (= c60b0665a_stake_attempt_rejected c60b0665a_stake_attempt_rejected))
(assert
 (= c60b0665a_staking_limit_hype c60b0665a_staking_limit_hype))
(assert
 (= c60b0665a_total_staked_before_hype c60b0665a_total_staked_before_hype))
(define-fun report_preconditions () Bool (and (= 100 c60b0665a_staking_limit_hype)
     (= 70 c60b0665a_total_staked_before_hype)
     (= 20 c60b0665a_slashing_amount_hype)
     (= 50 c60b0665a_effective_stake_hype)))
(define-fun report_safety () Bool (=> (= c60b0665a_remaining_capacity_hype
       (- c60b0665a_staking_limit_hype c60b0665a_total_staked_before_hype))
    (=> (and (< c60b0665a_effective_stake_hype c60b0665a_staking_limit_hype)
             (< 0 c60b0665a_remaining_capacity_hype))
        (not c60b0665a_stake_attempt_rejected))))
(define-fun report_effects () Bool (and (= c60b0665a_remaining_capacity_hype
        (- c60b0665a_staking_limit_hype c60b0665a_total_staked_before_hype))
     (< c60b0665a_effective_stake_hype c60b0665a_staking_limit_hype)
     (< 0 c60b0665a_remaining_capacity_hype)
     c60b0665a_stake_attempt_rejected
     c60b0665a_stake_attempt_rejected))
