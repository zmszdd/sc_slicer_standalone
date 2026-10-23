; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c642e606f_alice_locked_amount_epoch_n () Int)
(declare-fun c642e606f_eligible_prev_epoch () Int)
(declare-fun c642e606f_personal_utilization_observed () Int)
(declare-fun c642e606f_personal_utilization_prior () Int)
(declare-fun c642e606f_raw_utilization_delta () Int)
(declare-fun c642e606f_rewards_swept_to_protocol () Int)
(declare-fun c642e606f_user_claimed_prev_epoch () Int)
(assert
 (= c642e606f_alice_locked_amount_epoch_n c642e606f_alice_locked_amount_epoch_n))
(assert
 (= c642e606f_eligible_prev_epoch c642e606f_eligible_prev_epoch))
(assert
 (= c642e606f_personal_utilization_observed c642e606f_personal_utilization_observed))
(assert
 (= c642e606f_personal_utilization_prior c642e606f_personal_utilization_prior))
(assert
 (= c642e606f_raw_utilization_delta c642e606f_raw_utilization_delta))
(assert
 (= c642e606f_rewards_swept_to_protocol c642e606f_rewards_swept_to_protocol))
(assert
 (= c642e606f_user_claimed_prev_epoch c642e606f_user_claimed_prev_epoch))
(define-fun report_preconditions () Bool (and (= 100000 c642e606f_alice_locked_amount_epoch_n)
     (= 0 c642e606f_eligible_prev_epoch)
     (= 0 c642e606f_user_claimed_prev_epoch)
     (= 0 c642e606f_personal_utilization_prior)
     (= 0 c642e606f_raw_utilization_delta)))
(define-fun report_safety () Bool (=> (and (= 343 c642e606f_rewards_swept_to_protocol)
         (= 30 c642e606f_personal_utilization_observed))
    (=> (and (= 0 c642e606f_eligible_prev_epoch)
             (= 0 c642e606f_user_claimed_prev_epoch))
        (= 100 c642e606f_personal_utilization_observed))))
(define-fun report_effects () Bool (and (= 343 c642e606f_rewards_swept_to_protocol)
     (= 30 c642e606f_personal_utilization_observed)
     (= 0 c642e606f_eligible_prev_epoch)
     (= 0 c642e606f_user_claimed_prev_epoch)
     (not (= 100 c642e606f_personal_utilization_observed))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
