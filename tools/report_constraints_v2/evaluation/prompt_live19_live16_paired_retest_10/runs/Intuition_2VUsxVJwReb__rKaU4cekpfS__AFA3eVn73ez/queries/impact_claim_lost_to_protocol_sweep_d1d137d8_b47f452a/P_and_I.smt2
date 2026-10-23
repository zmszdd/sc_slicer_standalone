; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c56d90cc1_alice_locked_amount_epoch_n () Int)
(declare-fun c56d90cc1_eligible_prev_epoch () Int)
(declare-fun c56d90cc1_personal_utilization_observed () Int)
(declare-fun c56d90cc1_personal_utilization_prior () Int)
(declare-fun c56d90cc1_raw_utilization_delta () Int)
(declare-fun c56d90cc1_swept_amount () Int)
(declare-fun c56d90cc1_target_utilization () Int)
(declare-fun c56d90cc1_user_claimed_prev_epoch () Int)
(assert
 (= c56d90cc1_alice_locked_amount_epoch_n c56d90cc1_alice_locked_amount_epoch_n))
(assert
 (= c56d90cc1_eligible_prev_epoch c56d90cc1_eligible_prev_epoch))
(assert
 (= c56d90cc1_personal_utilization_observed c56d90cc1_personal_utilization_observed))
(assert
 (= c56d90cc1_personal_utilization_prior c56d90cc1_personal_utilization_prior))
(assert
 (= c56d90cc1_raw_utilization_delta c56d90cc1_raw_utilization_delta))
(assert
 (= c56d90cc1_swept_amount c56d90cc1_swept_amount))
(assert
 (= c56d90cc1_target_utilization c56d90cc1_target_utilization))
(assert
 (= c56d90cc1_user_claimed_prev_epoch c56d90cc1_user_claimed_prev_epoch))
(define-fun report_preconditions () Bool (and (= 100000 c56d90cc1_alice_locked_amount_epoch_n)
     (= 0 c56d90cc1_eligible_prev_epoch)
     (= 0 c56d90cc1_user_claimed_prev_epoch)
     (= 0 c56d90cc1_personal_utilization_prior)
     (= 0 c56d90cc1_raw_utilization_delta)))
(define-fun report_safety () Bool (=> (and (= 343 c56d90cc1_swept_amount)
         (= 70 c56d90cc1_personal_utilization_observed))
    (=> (and (= 0 c56d90cc1_target_utilization)
             (= 0 c56d90cc1_eligible_prev_epoch))
        (= 100 c56d90cc1_personal_utilization_observed))))
(define-fun report_effects () Bool (and (= 343 c56d90cc1_swept_amount)
     (= 70 c56d90cc1_personal_utilization_observed)
     (= 0 c56d90cc1_target_utilization)
     (= 0 c56d90cc1_eligible_prev_epoch)
     (not (= 100 c56d90cc1_personal_utilization_observed))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
