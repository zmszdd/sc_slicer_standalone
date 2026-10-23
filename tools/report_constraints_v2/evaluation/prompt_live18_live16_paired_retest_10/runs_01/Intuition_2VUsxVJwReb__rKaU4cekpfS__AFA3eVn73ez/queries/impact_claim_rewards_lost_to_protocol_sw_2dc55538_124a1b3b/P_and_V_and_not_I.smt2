; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c88e05632_alice_claimed_prev_epoch () Int)
(declare-fun c88e05632_alice_eligible_prev_epoch () Int)
(declare-fun c88e05632_alice_locked_amount_epoch_n () Int)
(declare-fun c88e05632_alice_personal_utilization () Int)
(declare-fun c88e05632_alice_raw_utilization_delta () Int)
(declare-fun c88e05632_first_timer_check_executed () Bool)
(declare-fun c88e05632_rewards_swept_to_protocol () Int)
(assert
 (= c88e05632_alice_claimed_prev_epoch c88e05632_alice_claimed_prev_epoch))
(assert
 (= c88e05632_alice_eligible_prev_epoch c88e05632_alice_eligible_prev_epoch))
(assert
 (= c88e05632_alice_locked_amount_epoch_n c88e05632_alice_locked_amount_epoch_n))
(assert
 (= c88e05632_alice_personal_utilization c88e05632_alice_personal_utilization))
(assert
 (= c88e05632_alice_raw_utilization_delta c88e05632_alice_raw_utilization_delta))
(assert
 (= c88e05632_first_timer_check_executed c88e05632_first_timer_check_executed))
(assert
 (= c88e05632_rewards_swept_to_protocol c88e05632_rewards_swept_to_protocol))
(define-fun report_preconditions () Bool (and (= 100000 c88e05632_alice_locked_amount_epoch_n)
     (= 0 c88e05632_alice_eligible_prev_epoch)
     (= 0 c88e05632_alice_claimed_prev_epoch)
     (= 0 c88e05632_alice_personal_utilization)
     (= 0 c88e05632_alice_raw_utilization_delta)))
(define-fun report_safety () Bool (=> (= 343 c88e05632_rewards_swept_to_protocol)
    (=> (and (= 0 c88e05632_alice_eligible_prev_epoch)
             (= 0 c88e05632_alice_claimed_prev_epoch)
             (>= 0 c88e05632_alice_raw_utilization_delta))
        c88e05632_first_timer_check_executed)))
(define-fun report_effects () Bool (and (= 343 c88e05632_rewards_swept_to_protocol)
     (= 0 c88e05632_alice_eligible_prev_epoch)
     (= 0 c88e05632_alice_claimed_prev_epoch)
     (>= 0 c88e05632_alice_raw_utilization_delta)
     (not c88e05632_first_timer_check_executed)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
