; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cfd504fda_actual_staked_after_slashing () Int)
(declare-fun cfd504fda_rewards_amount_before () Int)
(declare-fun cfd504fda_slashed_amount () Int)
(declare-fun cfd504fda_stake_attempted () Bool)
(declare-fun cfd504fda_stake_rejected () Bool)
(declare-fun cfd504fda_stake_succeeds () Bool)
(declare-fun cfd504fda_staking_limit () Int)
(declare-fun cfd504fda_total_claimed_before () Int)
(declare-fun cfd504fda_total_staked_before () Int)
(assert
 (= cfd504fda_actual_staked_after_slashing cfd504fda_actual_staked_after_slashing))
(assert
 (= cfd504fda_rewards_amount_before cfd504fda_rewards_amount_before))
(assert
 (= cfd504fda_slashed_amount cfd504fda_slashed_amount))
(assert
 (= cfd504fda_stake_attempted cfd504fda_stake_attempted))
(assert
 (= cfd504fda_stake_rejected cfd504fda_stake_rejected))
(assert
 (= cfd504fda_stake_succeeds cfd504fda_stake_succeeds))
(assert
 (= cfd504fda_staking_limit cfd504fda_staking_limit))
(assert
 (= cfd504fda_total_claimed_before cfd504fda_total_claimed_before))
(assert
 (= cfd504fda_total_staked_before cfd504fda_total_staked_before))
(define-fun report_preconditions () Bool (and (= 1000 cfd504fda_staking_limit)
     (= 800 cfd504fda_total_staked_before)
     (= 100 cfd504fda_rewards_amount_before)
     (= 0 cfd504fda_total_claimed_before)
     (= 200 cfd504fda_slashed_amount)
     (= 600 cfd504fda_actual_staked_after_slashing)))
(define-fun report_safety () Bool (=> (and cfd504fda_stake_attempted
         (< cfd504fda_actual_staked_after_slashing cfd504fda_staking_limit))
    cfd504fda_stake_succeeds))
(define-fun report_effects () Bool (and cfd504fda_stake_attempted
     (< cfd504fda_actual_staked_after_slashing cfd504fda_staking_limit)
     (not cfd504fda_stake_succeeds)
     cfd504fda_stake_rejected
     (< cfd504fda_actual_staked_after_slashing cfd504fda_staking_limit)
     cfd504fda_stake_attempted))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
