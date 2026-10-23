; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8cee8188_empty_period_elapsed () Bool)
(declare-fun c8cee8188_notify_reward_called () Bool)
(declare-fun c8cee8188_protocol_fund_loss_occurs () Bool)
(declare-fun c8cee8188_rewards_claimable_after () Bool)
(declare-fun c8cee8188_total_supply_zero () Bool)
(assert
 (= c8cee8188_empty_period_elapsed c8cee8188_empty_period_elapsed))
(assert
 (= c8cee8188_notify_reward_called c8cee8188_notify_reward_called))
(assert
 (= c8cee8188_protocol_fund_loss_occurs c8cee8188_protocol_fund_loss_occurs))
(assert
 (= c8cee8188_rewards_claimable_after c8cee8188_rewards_claimable_after))
(assert
 (= c8cee8188_total_supply_zero c8cee8188_total_supply_zero))
(define-fun report_preconditions () Bool (and c8cee8188_total_supply_zero
     c8cee8188_empty_period_elapsed
     c8cee8188_notify_reward_called))
(define-fun report_safety () Bool (=> (and c8cee8188_total_supply_zero
         c8cee8188_empty_period_elapsed
         c8cee8188_notify_reward_called)
    (and c8cee8188_rewards_claimable_after
         (not c8cee8188_protocol_fund_loss_occurs))))
(define-fun report_effects () Bool (and c8cee8188_total_supply_zero
     c8cee8188_empty_period_elapsed
     c8cee8188_notify_reward_called
     (not (and c8cee8188_rewards_claimable_after
               (not c8cee8188_protocol_fund_loss_occurs)))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
