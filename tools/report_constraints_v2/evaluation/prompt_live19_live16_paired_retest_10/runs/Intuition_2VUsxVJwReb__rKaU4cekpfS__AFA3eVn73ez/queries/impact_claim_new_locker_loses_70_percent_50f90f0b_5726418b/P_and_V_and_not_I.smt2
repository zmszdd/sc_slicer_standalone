; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c5259333e_alice_claimed_rewards_epoch_n_minus_1 () Int)
(declare-fun c5259333e_alice_eligible_epoch_n_minus_1 () Int)
(declare-fun c5259333e_alice_first_lock_amount () Int)
(declare-fun c5259333e_alice_personal_utilization () Int)
(declare-fun c5259333e_alice_raw_utilization_delta () Int)
(declare-fun c5259333e_first_timer_protection_reachable () Bool)
(assert
 (= c5259333e_alice_claimed_rewards_epoch_n_minus_1 c5259333e_alice_claimed_rewards_epoch_n_minus_1))
(assert
 (= c5259333e_alice_eligible_epoch_n_minus_1 c5259333e_alice_eligible_epoch_n_minus_1))
(assert
 (= c5259333e_alice_first_lock_amount c5259333e_alice_first_lock_amount))
(assert
 (= c5259333e_alice_personal_utilization c5259333e_alice_personal_utilization))
(assert
 (= c5259333e_alice_raw_utilization_delta c5259333e_alice_raw_utilization_delta))
(assert
 (= c5259333e_first_timer_protection_reachable c5259333e_first_timer_protection_reachable))
(define-fun report_preconditions () Bool (and (= 100000 c5259333e_alice_first_lock_amount)
     (= 0 c5259333e_alice_eligible_epoch_n_minus_1)
     (= 0 c5259333e_alice_claimed_rewards_epoch_n_minus_1)
     (= 0 c5259333e_alice_personal_utilization)
     (= 0 c5259333e_alice_raw_utilization_delta)))
(define-fun report_safety () Bool (=> (and (= 0 c5259333e_alice_personal_utilization)
         (= 0 c5259333e_alice_raw_utilization_delta))
    (=> (and (= 0 c5259333e_alice_eligible_epoch_n_minus_1)
             (= 0 c5259333e_alice_claimed_rewards_epoch_n_minus_1)
             (= 0 c5259333e_alice_personal_utilization)
             (= 0 c5259333e_alice_raw_utilization_delta))
        c5259333e_first_timer_protection_reachable)))
(define-fun report_effects () Bool (and (= 0 c5259333e_alice_personal_utilization)
     (= 0 c5259333e_alice_raw_utilization_delta)
     (= 0 c5259333e_alice_eligible_epoch_n_minus_1)
     (= 0 c5259333e_alice_claimed_rewards_epoch_n_minus_1)
     (= 0 c5259333e_alice_personal_utilization)
     (= 0 c5259333e_alice_raw_utilization_delta)
     (not c5259333e_first_timer_protection_reachable)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
