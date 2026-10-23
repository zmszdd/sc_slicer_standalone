; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c23318091_empty_period_elapsed () Bool)
(declare-fun c23318091_empty_period_rewards_accrued () Bool)
(declare-fun c23318091_notify_reward_called () Bool)
(declare-fun c23318091_protocol_fund_loss () Bool)
(declare-fun c23318091_total_supply_zero () Bool)
(assert
 (= c23318091_empty_period_elapsed c23318091_empty_period_elapsed))
(assert
 (= c23318091_empty_period_rewards_accrued c23318091_empty_period_rewards_accrued))
(assert
 (= c23318091_notify_reward_called c23318091_notify_reward_called))
(assert
 (= c23318091_protocol_fund_loss c23318091_protocol_fund_loss))
(assert
 (= c23318091_total_supply_zero c23318091_total_supply_zero))
(define-fun report_preconditions () Bool (and c23318091_total_supply_zero
     c23318091_empty_period_elapsed
     c23318091_notify_reward_called))
(define-fun report_safety () Bool (=> (and c23318091_total_supply_zero
         c23318091_empty_period_elapsed
         c23318091_notify_reward_called)
    (and c23318091_empty_period_rewards_accrued
         (not c23318091_protocol_fund_loss))))
(define-fun report_effects () Bool (and c23318091_total_supply_zero
     c23318091_empty_period_elapsed
     c23318091_notify_reward_called
     (not (and c23318091_empty_period_rewards_accrued
               (not c23318091_protocol_fund_loss)))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
