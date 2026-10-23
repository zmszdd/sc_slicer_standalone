; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca1c67d3e_empty_period_elapsed () Bool)
(declare-fun ca1c67d3e_epoch_rewards_stuck () Bool)
(declare-fun ca1c67d3e_notify_reward_called () Bool)
(declare-fun ca1c67d3e_total_supply () Int)
(assert
 (= ca1c67d3e_empty_period_elapsed ca1c67d3e_empty_period_elapsed))
(assert
 (= ca1c67d3e_epoch_rewards_stuck ca1c67d3e_epoch_rewards_stuck))
(assert
 (= ca1c67d3e_notify_reward_called ca1c67d3e_notify_reward_called))
(assert
 (= ca1c67d3e_total_supply ca1c67d3e_total_supply))
(define-fun report_preconditions () Bool (and (= 0 ca1c67d3e_total_supply)
     ca1c67d3e_empty_period_elapsed
     ca1c67d3e_notify_reward_called))
(define-fun report_safety () Bool (=> (and (= 0 ca1c67d3e_total_supply)
         ca1c67d3e_empty_period_elapsed
         ca1c67d3e_notify_reward_called)
    (not ca1c67d3e_epoch_rewards_stuck)))
(define-fun report_effects () Bool (and (= 0 ca1c67d3e_total_supply)
     ca1c67d3e_empty_period_elapsed
     ca1c67d3e_notify_reward_called
     (not (not ca1c67d3e_epoch_rewards_stuck))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
