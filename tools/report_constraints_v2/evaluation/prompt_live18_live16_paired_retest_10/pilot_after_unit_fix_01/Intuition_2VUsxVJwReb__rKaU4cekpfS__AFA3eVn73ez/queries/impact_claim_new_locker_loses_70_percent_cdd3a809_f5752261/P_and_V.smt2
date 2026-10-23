; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c07c528e9_alice_claimed_prev_epoch () Int)
(declare-fun c07c528e9_alice_eligible_prev_epoch () Int)
(declare-fun c07c528e9_alice_first_epoch_reward_share_lost () Int)
(declare-fun c07c528e9_alice_personal_utilization () Int)
(declare-fun c07c528e9_alice_personal_utilization_ratio_observed () Int)
(declare-fun c07c528e9_alice_prior_vetrust_balance () Int)
(assert
 (= c07c528e9_alice_claimed_prev_epoch c07c528e9_alice_claimed_prev_epoch))
(assert
 (= c07c528e9_alice_eligible_prev_epoch c07c528e9_alice_eligible_prev_epoch))
(assert
 (= c07c528e9_alice_first_epoch_reward_share_lost c07c528e9_alice_first_epoch_reward_share_lost))
(assert
 (= c07c528e9_alice_personal_utilization c07c528e9_alice_personal_utilization))
(assert
 (= c07c528e9_alice_personal_utilization_ratio_observed c07c528e9_alice_personal_utilization_ratio_observed))
(assert
 (= c07c528e9_alice_prior_vetrust_balance c07c528e9_alice_prior_vetrust_balance))
(define-fun report_preconditions () Bool (and (= 0 c07c528e9_alice_prior_vetrust_balance)
     (= 0 c07c528e9_alice_personal_utilization)
     (= 0 c07c528e9_alice_eligible_prev_epoch)
     (= 0 c07c528e9_alice_claimed_prev_epoch)))
(define-fun report_safety () Bool (=> (and (= 0 c07c528e9_alice_personal_utilization)
         (= 70 c07c528e9_alice_first_epoch_reward_share_lost))
    (=> (and (= 0 c07c528e9_alice_prior_vetrust_balance)
             (= 0 c07c528e9_alice_eligible_prev_epoch)
             (= 0 c07c528e9_alice_claimed_prev_epoch))
        (= 100 c07c528e9_alice_personal_utilization_ratio_observed))))
(define-fun report_effects () Bool (and (= 0 c07c528e9_alice_personal_utilization)
     (= 70 c07c528e9_alice_first_epoch_reward_share_lost)
     (= 0 c07c528e9_alice_prior_vetrust_balance)
     (= 0 c07c528e9_alice_eligible_prev_epoch)
     (= 0 c07c528e9_alice_claimed_prev_epoch)
     (not (= 100 c07c528e9_alice_personal_utilization_ratio_observed))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
