; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cf2c71cc9_alice_locked_amount_epoch_n () Int)
(declare-fun cf2c71cc9_eligible_prev_epoch () Int)
(declare-fun cf2c71cc9_personal_utilization_prev () Int)
(declare-fun cf2c71cc9_target_prev_epoch () Int)
(declare-fun cf2c71cc9_user_claimed_prev_epoch () Int)
(declare-fun cf2c71cc9_utilization_ratio_intended () Int)
(declare-fun cf2c71cc9_utilization_ratio_observed () Int)
(assert
 (= cf2c71cc9_alice_locked_amount_epoch_n cf2c71cc9_alice_locked_amount_epoch_n))
(assert
 (= cf2c71cc9_eligible_prev_epoch cf2c71cc9_eligible_prev_epoch))
(assert
 (= cf2c71cc9_personal_utilization_prev cf2c71cc9_personal_utilization_prev))
(assert
 (= cf2c71cc9_target_prev_epoch cf2c71cc9_target_prev_epoch))
(assert
 (= cf2c71cc9_user_claimed_prev_epoch cf2c71cc9_user_claimed_prev_epoch))
(assert
 (= cf2c71cc9_utilization_ratio_intended cf2c71cc9_utilization_ratio_intended))
(assert
 (= cf2c71cc9_utilization_ratio_observed cf2c71cc9_utilization_ratio_observed))
(define-fun report_preconditions () Bool (and (< 0 cf2c71cc9_alice_locked_amount_epoch_n)
     (= 0 cf2c71cc9_eligible_prev_epoch)
     (= 0 cf2c71cc9_user_claimed_prev_epoch)
     (= 0 cf2c71cc9_personal_utilization_prev)))
(define-fun report_safety () Bool (=> (and (= 0 cf2c71cc9_target_prev_epoch)
         (= 0 cf2c71cc9_eligible_prev_epoch)
         (= 0 cf2c71cc9_personal_utilization_prev))
    (=> (and (= 0 cf2c71cc9_target_prev_epoch)
             (= 0 cf2c71cc9_eligible_prev_epoch))
        (>= (* cf2c71cc9_utilization_ratio_observed 100)
            (* cf2c71cc9_utilization_ratio_intended 100)))))
(define-fun report_effects () Bool (and (= 0 cf2c71cc9_target_prev_epoch)
     (= 0 cf2c71cc9_eligible_prev_epoch)
     (= 0 cf2c71cc9_personal_utilization_prev)
     (= 0 cf2c71cc9_target_prev_epoch)
     (= 0 cf2c71cc9_eligible_prev_epoch)
     (not (>= (* cf2c71cc9_utilization_ratio_observed 100)
              (* cf2c71cc9_utilization_ratio_intended 100)))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
