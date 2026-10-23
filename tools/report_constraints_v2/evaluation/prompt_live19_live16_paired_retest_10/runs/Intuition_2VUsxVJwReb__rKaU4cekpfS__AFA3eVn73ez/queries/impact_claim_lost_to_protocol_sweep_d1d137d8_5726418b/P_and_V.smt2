; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7390f78f_alice_claimed_rewards_epoch_n_minus_1 () Int)
(declare-fun c7390f78f_alice_eligible_epoch_n_minus_1 () Int)
(declare-fun c7390f78f_alice_locked_amount_epoch_n () Int)
(declare-fun c7390f78f_alice_personal_utilization () Int)
(declare-fun c7390f78f_alice_raw_utilization_delta () Int)
(declare-fun c7390f78f_first_timer_protection_reachable () Bool)
(declare-fun c7390f78f_protocol_swept_amount () Int)
(assert
 (= c7390f78f_alice_claimed_rewards_epoch_n_minus_1 c7390f78f_alice_claimed_rewards_epoch_n_minus_1))
(assert
 (= c7390f78f_alice_eligible_epoch_n_minus_1 c7390f78f_alice_eligible_epoch_n_minus_1))
(assert
 (= c7390f78f_alice_locked_amount_epoch_n c7390f78f_alice_locked_amount_epoch_n))
(assert
 (= c7390f78f_alice_personal_utilization c7390f78f_alice_personal_utilization))
(assert
 (= c7390f78f_alice_raw_utilization_delta c7390f78f_alice_raw_utilization_delta))
(assert
 (= c7390f78f_first_timer_protection_reachable c7390f78f_first_timer_protection_reachable))
(assert
 (= c7390f78f_protocol_swept_amount c7390f78f_protocol_swept_amount))
(define-fun report_preconditions () Bool (and (= 100000 c7390f78f_alice_locked_amount_epoch_n)
     (= 0 c7390f78f_alice_eligible_epoch_n_minus_1)
     (= 0 c7390f78f_alice_claimed_rewards_epoch_n_minus_1)
     (= 0 c7390f78f_alice_personal_utilization)
     (= 0 c7390f78f_alice_raw_utilization_delta)))
(define-fun report_safety () Bool (=> (= 343 c7390f78f_protocol_swept_amount)
    (=> c7390f78f_first_timer_protection_reachable
        (= 0 c7390f78f_protocol_swept_amount))))
(define-fun report_effects () Bool (and (= 343 c7390f78f_protocol_swept_amount)
     c7390f78f_first_timer_protection_reachable
     (not (= 0 c7390f78f_protocol_swept_amount))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
