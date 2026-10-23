; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cf7e3bcb4_alice_claimed_prev_epoch () Int)
(declare-fun cf7e3bcb4_alice_eligible_prev_epoch () Int)
(declare-fun cf7e3bcb4_alice_first_epoch_rewards_lost_fraction () Int)
(declare-fun cf7e3bcb4_alice_locked_amount_epoch_n () Int)
(declare-fun cf7e3bcb4_alice_personal_utilization_observed () Int)
(declare-fun cf7e3bcb4_alice_personal_utilization_prev () Int)
(declare-fun cf7e3bcb4_alice_raw_utilization_delta () Int)
(declare-fun cf7e3bcb4_alice_target_prev_epoch () Int)
(assert
 (= cf7e3bcb4_alice_claimed_prev_epoch cf7e3bcb4_alice_claimed_prev_epoch))
(assert
 (= cf7e3bcb4_alice_eligible_prev_epoch cf7e3bcb4_alice_eligible_prev_epoch))
(assert
 (= cf7e3bcb4_alice_first_epoch_rewards_lost_fraction cf7e3bcb4_alice_first_epoch_rewards_lost_fraction))
(assert
 (= cf7e3bcb4_alice_locked_amount_epoch_n cf7e3bcb4_alice_locked_amount_epoch_n))
(assert
 (= cf7e3bcb4_alice_personal_utilization_observed cf7e3bcb4_alice_personal_utilization_observed))
(assert
 (= cf7e3bcb4_alice_personal_utilization_prev cf7e3bcb4_alice_personal_utilization_prev))
(assert
 (= cf7e3bcb4_alice_raw_utilization_delta cf7e3bcb4_alice_raw_utilization_delta))
(assert
 (= cf7e3bcb4_alice_target_prev_epoch cf7e3bcb4_alice_target_prev_epoch))
(define-fun report_preconditions () Bool (and (= 100000 cf7e3bcb4_alice_locked_amount_epoch_n)
     (= 0 cf7e3bcb4_alice_eligible_prev_epoch)
     (= 0 cf7e3bcb4_alice_claimed_prev_epoch)
     (= 0 cf7e3bcb4_alice_personal_utilization_prev)
     (= 0 cf7e3bcb4_alice_raw_utilization_delta)))
(define-fun report_safety () Bool (=> (and (= 30 cf7e3bcb4_alice_personal_utilization_observed)
         (= 70 cf7e3bcb4_alice_first_epoch_rewards_lost_fraction))
    (=> (and (= 0 cf7e3bcb4_alice_target_prev_epoch)
             (= 0 cf7e3bcb4_alice_eligible_prev_epoch))
        (= 100 cf7e3bcb4_alice_personal_utilization_observed))))
(define-fun report_effects () Bool (and (= 30 cf7e3bcb4_alice_personal_utilization_observed)
     (= 70 cf7e3bcb4_alice_first_epoch_rewards_lost_fraction)
     (= 0 cf7e3bcb4_alice_target_prev_epoch)
     (= 0 cf7e3bcb4_alice_eligible_prev_epoch)
     (not (= 100 cf7e3bcb4_alice_personal_utilization_observed))))
