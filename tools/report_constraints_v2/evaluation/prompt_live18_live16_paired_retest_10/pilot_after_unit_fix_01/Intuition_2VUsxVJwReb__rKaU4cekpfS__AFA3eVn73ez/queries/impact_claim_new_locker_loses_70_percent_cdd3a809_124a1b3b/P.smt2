; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7f134544_alice_claimed_prev_epoch () Int)
(declare-fun c7f134544_alice_eligible_prev_epoch () Int)
(declare-fun c7f134544_alice_personal_utilization () Int)
(declare-fun c7f134544_alice_prior_vetrust_balance () Int)
(declare-fun c7f134544_first_epoch_reward_loss_fraction () Int)
(declare-fun c7f134544_first_timer_check_evaluated () Bool)
(declare-fun c7f134544_raw_utilization_delta () Int)
(assert
 (= c7f134544_alice_claimed_prev_epoch c7f134544_alice_claimed_prev_epoch))
(assert
 (= c7f134544_alice_eligible_prev_epoch c7f134544_alice_eligible_prev_epoch))
(assert
 (= c7f134544_alice_personal_utilization c7f134544_alice_personal_utilization))
(assert
 (= c7f134544_alice_prior_vetrust_balance c7f134544_alice_prior_vetrust_balance))
(assert
 (= c7f134544_first_epoch_reward_loss_fraction c7f134544_first_epoch_reward_loss_fraction))
(assert
 (= c7f134544_first_timer_check_evaluated c7f134544_first_timer_check_evaluated))
(assert
 (= c7f134544_raw_utilization_delta c7f134544_raw_utilization_delta))
(define-fun report_preconditions () Bool (and (= 0 c7f134544_alice_prior_vetrust_balance)
     (= 0 c7f134544_alice_personal_utilization)
     (= 0 c7f134544_alice_eligible_prev_epoch)
     (= 0 c7f134544_alice_claimed_prev_epoch)))
(define-fun report_safety () Bool (=> (and (= 0 c7f134544_alice_prior_vetrust_balance)
         (= 0 c7f134544_alice_personal_utilization)
         (= 70 c7f134544_first_epoch_reward_loss_fraction))
    (=> (and (= 0 c7f134544_alice_prior_vetrust_balance)
             (= 0 c7f134544_alice_personal_utilization)
             (>= 0 c7f134544_raw_utilization_delta))
        c7f134544_first_timer_check_evaluated)))
(define-fun report_effects () Bool (and (= 0 c7f134544_alice_prior_vetrust_balance)
     (= 0 c7f134544_alice_personal_utilization)
     (= 70 c7f134544_first_epoch_reward_loss_fraction)
     (= 0 c7f134544_alice_prior_vetrust_balance)
     (= 0 c7f134544_alice_personal_utilization)
     (>= 0 c7f134544_raw_utilization_delta)
     (not c7f134544_first_timer_check_evaluated)))
(assert report_preconditions)
(check-sat)
(get-model)
