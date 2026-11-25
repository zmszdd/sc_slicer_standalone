; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce15953c3_effective_stake_hype () Int)
(declare-fun ce15953c3_net_staked_used_hype () Int)
(declare-fun ce15953c3_slashing_amount_hype () Int)
(declare-fun ce15953c3_stake_attempt_rejected () Bool)
(declare-fun ce15953c3_staking_limit_hype () Int)
(declare-fun ce15953c3_total_staked_before_hype () Int)
(assert
 (= ce15953c3_effective_stake_hype ce15953c3_effective_stake_hype))
(assert
 (= ce15953c3_net_staked_used_hype ce15953c3_net_staked_used_hype))
(assert
 (= ce15953c3_slashing_amount_hype ce15953c3_slashing_amount_hype))
(assert
 (= ce15953c3_stake_attempt_rejected ce15953c3_stake_attempt_rejected))
(assert
 (= ce15953c3_staking_limit_hype ce15953c3_staking_limit_hype))
(assert
 (= ce15953c3_total_staked_before_hype ce15953c3_total_staked_before_hype))
(define-fun report_preconditions () Bool (and (= 100 ce15953c3_staking_limit_hype)
     (= 70 ce15953c3_total_staked_before_hype)
     (= 20 ce15953c3_slashing_amount_hype)
     (= 50 ce15953c3_effective_stake_hype)
     ce15953c3_stake_attempt_rejected))
(define-fun report_safety () Bool (=> (= ce15953c3_effective_stake_hype
       (- ce15953c3_total_staked_before_hype ce15953c3_slashing_amount_hype))
    (= ce15953c3_net_staked_used_hype ce15953c3_effective_stake_hype)))
(define-fun report_effects () Bool (and (= ce15953c3_effective_stake_hype
        (- ce15953c3_total_staked_before_hype ce15953c3_slashing_amount_hype))
     ce15953c3_stake_attempt_rejected
     (not (= ce15953c3_net_staked_used_hype ce15953c3_effective_stake_hype))
     ce15953c3_stake_attempt_rejected))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
