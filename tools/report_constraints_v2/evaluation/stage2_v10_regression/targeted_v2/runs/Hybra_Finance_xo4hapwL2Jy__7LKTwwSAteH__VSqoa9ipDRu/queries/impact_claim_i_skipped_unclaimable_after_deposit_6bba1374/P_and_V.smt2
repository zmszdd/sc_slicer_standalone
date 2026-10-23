; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6d3a133e_empty_period_elapsed () Bool)
(declare-fun c6d3a133e_notify_reward_called () Bool)
(declare-fun c6d3a133e_skipped_rewards_claimable () Bool)
(declare-fun c6d3a133e_total_supply () Int)
(assert
 (= c6d3a133e_empty_period_elapsed c6d3a133e_empty_period_elapsed))
(assert
 (= c6d3a133e_notify_reward_called c6d3a133e_notify_reward_called))
(assert
 (= c6d3a133e_skipped_rewards_claimable c6d3a133e_skipped_rewards_claimable))
(assert
 (= c6d3a133e_total_supply c6d3a133e_total_supply))
(define-fun report_preconditions () Bool (and (= 0 c6d3a133e_total_supply)
     c6d3a133e_empty_period_elapsed
     c6d3a133e_notify_reward_called))
(define-fun report_safety () Bool (=> (and (= 0 c6d3a133e_total_supply)
         c6d3a133e_empty_period_elapsed
         c6d3a133e_notify_reward_called)
    c6d3a133e_skipped_rewards_claimable))
(define-fun report_effects () Bool (and (= 0 c6d3a133e_total_supply)
     c6d3a133e_empty_period_elapsed
     c6d3a133e_notify_reward_called
     (not c6d3a133e_skipped_rewards_claimable)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
