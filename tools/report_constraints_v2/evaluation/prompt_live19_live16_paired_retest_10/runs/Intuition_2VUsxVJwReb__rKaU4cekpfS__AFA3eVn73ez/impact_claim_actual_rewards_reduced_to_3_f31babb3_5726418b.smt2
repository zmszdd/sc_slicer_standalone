; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c37bd8885_actual_rewards_trust () Int)
(declare-fun c37bd8885_alice_claimed_rewards_epoch_n_minus_1 () Int)
(declare-fun c37bd8885_alice_eligible_epoch_n_minus_1 () Int)
(declare-fun c37bd8885_alice_locked_amount_epoch_n () Int)
(declare-fun c37bd8885_alice_personal_utilization () Int)
(declare-fun c37bd8885_alice_raw_utilization_delta () Int)
(declare-fun c37bd8885_first_timer_protection_reachable () Bool)
(assert
 (= c37bd8885_actual_rewards_trust c37bd8885_actual_rewards_trust))
(assert
 (= c37bd8885_alice_claimed_rewards_epoch_n_minus_1 c37bd8885_alice_claimed_rewards_epoch_n_minus_1))
(assert
 (= c37bd8885_alice_eligible_epoch_n_minus_1 c37bd8885_alice_eligible_epoch_n_minus_1))
(assert
 (= c37bd8885_alice_locked_amount_epoch_n c37bd8885_alice_locked_amount_epoch_n))
(assert
 (= c37bd8885_alice_personal_utilization c37bd8885_alice_personal_utilization))
(assert
 (= c37bd8885_alice_raw_utilization_delta c37bd8885_alice_raw_utilization_delta))
(assert
 (= c37bd8885_first_timer_protection_reachable c37bd8885_first_timer_protection_reachable))
(define-fun report_preconditions () Bool (and (= 100000 c37bd8885_alice_locked_amount_epoch_n)
     (= 0 c37bd8885_alice_eligible_epoch_n_minus_1)
     (= 0 c37bd8885_alice_claimed_rewards_epoch_n_minus_1)
     (= 0 c37bd8885_alice_personal_utilization)
     (= 0 c37bd8885_alice_raw_utilization_delta)))
(define-fun report_safety () Bool (=> (= 147 c37bd8885_actual_rewards_trust)
    (=> (and (= 100000 c37bd8885_alice_locked_amount_epoch_n)
             (= 0 c37bd8885_alice_eligible_epoch_n_minus_1)
             (= 0 c37bd8885_alice_claimed_rewards_epoch_n_minus_1)
             (= 0 c37bd8885_alice_personal_utilization)
             (= 0 c37bd8885_alice_raw_utilization_delta))
        c37bd8885_first_timer_protection_reachable)))
(define-fun report_effects () Bool (and (= 147 c37bd8885_actual_rewards_trust)
     (= 100000 c37bd8885_alice_locked_amount_epoch_n)
     (= 0 c37bd8885_alice_eligible_epoch_n_minus_1)
     (= 0 c37bd8885_alice_claimed_rewards_epoch_n_minus_1)
     (= 0 c37bd8885_alice_personal_utilization)
     (= 0 c37bd8885_alice_raw_utilization_delta)
     (not c37bd8885_first_timer_protection_reachable)))
