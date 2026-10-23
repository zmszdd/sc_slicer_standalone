; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c47a9c79b_empty_period_elapsed () Bool)
(declare-fun c47a9c79b_notify_reward_called () Bool)
(declare-fun c47a9c79b_rewards_claimable () Bool)
(declare-fun c47a9c79b_rewards_unclaimable () Bool)
(declare-fun c47a9c79b_total_supply_zero () Bool)
(assert
 (= c47a9c79b_empty_period_elapsed c47a9c79b_empty_period_elapsed))
(assert
 (= c47a9c79b_notify_reward_called c47a9c79b_notify_reward_called))
(assert
 (= c47a9c79b_rewards_claimable c47a9c79b_rewards_claimable))
(assert
 (= c47a9c79b_rewards_unclaimable c47a9c79b_rewards_unclaimable))
(assert
 (= c47a9c79b_total_supply_zero c47a9c79b_total_supply_zero))
(define-fun report_preconditions () Bool (and c47a9c79b_total_supply_zero
     c47a9c79b_empty_period_elapsed
     c47a9c79b_notify_reward_called))
(define-fun report_safety () Bool (=> (and c47a9c79b_total_supply_zero
         c47a9c79b_empty_period_elapsed
         c47a9c79b_notify_reward_called)
    (and c47a9c79b_rewards_claimable (not c47a9c79b_rewards_unclaimable))))
(define-fun report_effects () Bool (and c47a9c79b_total_supply_zero
     c47a9c79b_empty_period_elapsed
     c47a9c79b_notify_reward_called
     (not (and c47a9c79b_rewards_claimable (not c47a9c79b_rewards_unclaimable)))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
