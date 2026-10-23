; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc155841c_alice_locked_amount () Int)
(declare-fun cc155841c_alice_personal_utilization () Int)
(declare-fun cc155841c_alice_prior_claimed_rewards () Int)
(declare-fun cc155841c_alice_prior_eligible () Int)
(declare-fun cc155841c_applied_personal_utilization_ratio () Int)
(declare-fun cc155841c_first_epoch_reward_loss_ratio () Int)
(assert
 (= cc155841c_alice_locked_amount cc155841c_alice_locked_amount))
(assert
 (= cc155841c_alice_personal_utilization cc155841c_alice_personal_utilization))
(assert
 (= cc155841c_alice_prior_claimed_rewards cc155841c_alice_prior_claimed_rewards))
(assert
 (= cc155841c_alice_prior_eligible cc155841c_alice_prior_eligible))
(assert
 (= cc155841c_applied_personal_utilization_ratio cc155841c_applied_personal_utilization_ratio))
(assert
 (= cc155841c_first_epoch_reward_loss_ratio cc155841c_first_epoch_reward_loss_ratio))
(define-fun report_preconditions () Bool (and (= 100000 cc155841c_alice_locked_amount)
     (= 0 cc155841c_alice_prior_eligible)
     (= 0 cc155841c_alice_prior_claimed_rewards)
     (= 0 cc155841c_alice_personal_utilization)))
(define-fun report_safety () Bool (=> (and (= 0 cc155841c_alice_prior_eligible)
         (= 0 cc155841c_alice_prior_claimed_rewards))
    (= 100 cc155841c_applied_personal_utilization_ratio)))
(define-fun report_effects () Bool (and (= 70 cc155841c_first_epoch_reward_loss_ratio)
     (= 0 cc155841c_alice_prior_eligible)
     (= 0 cc155841c_alice_personal_utilization)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
