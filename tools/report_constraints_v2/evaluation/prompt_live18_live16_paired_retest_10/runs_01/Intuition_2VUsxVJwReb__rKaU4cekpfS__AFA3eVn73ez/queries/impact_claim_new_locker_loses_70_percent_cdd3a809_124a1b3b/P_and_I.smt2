; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7f134544_alice_claimed_prev_epoch () Int)
(declare-fun c7f134544_alice_eligible_prev_epoch () Int)
(declare-fun c7f134544_alice_locked_amount_epoch_n () Int)
(declare-fun c7f134544_alice_personal_utilization () Int)
(declare-fun c7f134544_alice_raw_utilization_delta () Int)
(declare-fun c7f134544_first_epoch_reward_loss_fraction () Int)
(declare-fun c7f134544_first_timer_check_executed () Bool)
(assert
 (= c7f134544_alice_claimed_prev_epoch c7f134544_alice_claimed_prev_epoch))
(assert
 (= c7f134544_alice_eligible_prev_epoch c7f134544_alice_eligible_prev_epoch))
(assert
 (= c7f134544_alice_locked_amount_epoch_n c7f134544_alice_locked_amount_epoch_n))
(assert
 (= c7f134544_alice_personal_utilization c7f134544_alice_personal_utilization))
(assert
 (= c7f134544_alice_raw_utilization_delta c7f134544_alice_raw_utilization_delta))
(assert
 (= c7f134544_first_epoch_reward_loss_fraction c7f134544_first_epoch_reward_loss_fraction))
(assert
 (= c7f134544_first_timer_check_executed c7f134544_first_timer_check_executed))
(define-fun report_preconditions () Bool (and (= 100000 c7f134544_alice_locked_amount_epoch_n)
     (= 0 c7f134544_alice_eligible_prev_epoch)
     (= 0 c7f134544_alice_claimed_prev_epoch)
     (= 0 c7f134544_alice_personal_utilization)
     (= 0 c7f134544_alice_raw_utilization_delta)))
(define-fun report_safety () Bool (=> (and (>= 0 c7f134544_alice_raw_utilization_delta)
         (= 70 c7f134544_first_epoch_reward_loss_fraction))
    (=> (and (= 0 c7f134544_alice_eligible_prev_epoch)
             (= 0 c7f134544_alice_claimed_prev_epoch)
             (>= 0 c7f134544_alice_raw_utilization_delta))
        c7f134544_first_timer_check_executed)))
(define-fun report_effects () Bool (and (>= 0 c7f134544_alice_raw_utilization_delta)
     (= 70 c7f134544_first_epoch_reward_loss_fraction)
     (= 0 c7f134544_alice_eligible_prev_epoch)
     (= 0 c7f134544_alice_claimed_prev_epoch)
     (>= 0 c7f134544_alice_raw_utilization_delta)
     (not c7f134544_first_timer_check_executed)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
