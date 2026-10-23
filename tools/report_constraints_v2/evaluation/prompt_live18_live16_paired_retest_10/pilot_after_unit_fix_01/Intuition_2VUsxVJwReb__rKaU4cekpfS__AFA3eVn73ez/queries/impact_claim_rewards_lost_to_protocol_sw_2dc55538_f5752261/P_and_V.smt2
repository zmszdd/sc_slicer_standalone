; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1e630f9b_alice_claimed_rewards_prev_epoch () Int)
(declare-fun c1e630f9b_alice_eligible_prev_epoch () Int)
(declare-fun c1e630f9b_alice_locked_trust_amount () Int)
(declare-fun c1e630f9b_alice_personal_utilization () Int)
(declare-fun c1e630f9b_alice_personal_utilization_ratio () Int)
(declare-fun c1e630f9b_alice_rewards_swept_to_protocol () Int)
(assert
 (= c1e630f9b_alice_claimed_rewards_prev_epoch c1e630f9b_alice_claimed_rewards_prev_epoch))
(assert
 (= c1e630f9b_alice_eligible_prev_epoch c1e630f9b_alice_eligible_prev_epoch))
(assert
 (= c1e630f9b_alice_locked_trust_amount c1e630f9b_alice_locked_trust_amount))
(assert
 (= c1e630f9b_alice_personal_utilization c1e630f9b_alice_personal_utilization))
(assert
 (= c1e630f9b_alice_personal_utilization_ratio c1e630f9b_alice_personal_utilization_ratio))
(assert
 (= c1e630f9b_alice_rewards_swept_to_protocol c1e630f9b_alice_rewards_swept_to_protocol))
(define-fun report_preconditions () Bool (and (= 100000 c1e630f9b_alice_locked_trust_amount)
     (= 0 c1e630f9b_alice_personal_utilization)
     (= 0 c1e630f9b_alice_eligible_prev_epoch)
     (= 0 c1e630f9b_alice_claimed_rewards_prev_epoch)))
(define-fun report_safety () Bool (=> (and (= 343 c1e630f9b_alice_rewards_swept_to_protocol)
         (= 70 c1e630f9b_alice_personal_utilization_ratio))
    (=> (and (= 0 c1e630f9b_alice_eligible_prev_epoch)
             (= 0 c1e630f9b_alice_claimed_rewards_prev_epoch))
        (= 100 c1e630f9b_alice_personal_utilization_ratio))))
(define-fun report_effects () Bool (and (= 343 c1e630f9b_alice_rewards_swept_to_protocol)
     (= 70 c1e630f9b_alice_personal_utilization_ratio)
     (= 0 c1e630f9b_alice_eligible_prev_epoch)
     (= 0 c1e630f9b_alice_claimed_rewards_prev_epoch)
     (not (= 100 c1e630f9b_alice_personal_utilization_ratio))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
