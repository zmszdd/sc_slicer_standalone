; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cac69136e_reward_event_pending () Bool)
(declare-fun cac69136e_rewards_captured_by_frontrun_stake () Bool)
(declare-fun cac69136e_rewards_interval_exceeds_withdrawal_delay () Bool)
(assert
 (= cac69136e_reward_event_pending cac69136e_reward_event_pending))
(assert
 (= cac69136e_rewards_captured_by_frontrun_stake cac69136e_rewards_captured_by_frontrun_stake))
(assert
 (= cac69136e_rewards_interval_exceeds_withdrawal_delay cac69136e_rewards_interval_exceeds_withdrawal_delay))
(define-fun report_preconditions () Bool (and cac69136e_rewards_interval_exceeds_withdrawal_delay
     cac69136e_reward_event_pending))
(define-fun report_safety () Bool (=> (and cac69136e_rewards_interval_exceeds_withdrawal_delay
         cac69136e_reward_event_pending)
    (not cac69136e_rewards_captured_by_frontrun_stake)))
(define-fun report_effects () Bool (and cac69136e_rewards_interval_exceeds_withdrawal_delay
     cac69136e_reward_event_pending
     (not (not cac69136e_rewards_captured_by_frontrun_stake))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
