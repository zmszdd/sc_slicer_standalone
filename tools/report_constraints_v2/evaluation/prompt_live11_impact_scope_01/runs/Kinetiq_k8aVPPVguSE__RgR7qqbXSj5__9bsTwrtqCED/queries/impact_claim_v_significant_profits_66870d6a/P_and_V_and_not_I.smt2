; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca5a74860_reward_event_pending () Bool)
(declare-fun ca5a74860_rewards_interval_exceeds_withdrawal_delay () Bool)
(declare-fun ca5a74860_significant_profits_obtained () Bool)
(declare-fun ca5a74860_slashing_event_pending () Bool)
(declare-fun ca5a74860_staked_amounts_large () Bool)
(assert
 (= ca5a74860_reward_event_pending ca5a74860_reward_event_pending))
(assert
 (= ca5a74860_rewards_interval_exceeds_withdrawal_delay ca5a74860_rewards_interval_exceeds_withdrawal_delay))
(assert
 (= ca5a74860_significant_profits_obtained ca5a74860_significant_profits_obtained))
(assert
 (= ca5a74860_slashing_event_pending ca5a74860_slashing_event_pending))
(assert
 (= ca5a74860_staked_amounts_large ca5a74860_staked_amounts_large))
(define-fun report_preconditions () Bool (and ca5a74860_rewards_interval_exceeds_withdrawal_delay
     ca5a74860_reward_event_pending
     ca5a74860_slashing_event_pending
     ca5a74860_staked_amounts_large))
(define-fun report_safety () Bool (=> (and ca5a74860_rewards_interval_exceeds_withdrawal_delay
         ca5a74860_reward_event_pending
         ca5a74860_staked_amounts_large)
    (not ca5a74860_significant_profits_obtained)))
(define-fun report_effects () Bool (and ca5a74860_rewards_interval_exceeds_withdrawal_delay
     ca5a74860_reward_event_pending
     ca5a74860_staked_amounts_large
     (not (not ca5a74860_significant_profits_obtained))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
