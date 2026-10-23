; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c10a31276_empty_period_elapsed () Bool)
(declare-fun c10a31276_notify_reward_called () Bool)
(declare-fun c10a31276_rewards_claimable () Bool)
(declare-fun c10a31276_total_supply_zero () Bool)
(assert
 (= c10a31276_empty_period_elapsed c10a31276_empty_period_elapsed))
(assert
 (= c10a31276_notify_reward_called c10a31276_notify_reward_called))
(assert
 (= c10a31276_rewards_claimable c10a31276_rewards_claimable))
(assert
 (= c10a31276_total_supply_zero c10a31276_total_supply_zero))
(define-fun report_preconditions () Bool (and c10a31276_total_supply_zero
     c10a31276_empty_period_elapsed
     c10a31276_notify_reward_called))
(define-fun report_safety () Bool (=> (and c10a31276_total_supply_zero
         c10a31276_empty_period_elapsed
         c10a31276_notify_reward_called)
    c10a31276_rewards_claimable))
(define-fun report_effects () Bool (and c10a31276_total_supply_zero
     c10a31276_empty_period_elapsed
     c10a31276_notify_reward_called
     (not c10a31276_rewards_claimable)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
