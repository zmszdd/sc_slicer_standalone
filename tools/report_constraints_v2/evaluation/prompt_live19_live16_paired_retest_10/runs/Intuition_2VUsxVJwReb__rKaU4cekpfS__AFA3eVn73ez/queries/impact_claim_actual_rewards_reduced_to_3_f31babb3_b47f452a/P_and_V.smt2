; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c395215f6_actual_rewards_trust () Int)
(declare-fun c395215f6_alice_locked_amount_epoch_n () Int)
(declare-fun c395215f6_eligible_prev_epoch () Int)
(declare-fun c395215f6_personal_utilization_prior () Int)
(declare-fun c395215f6_personal_utilization_ratio () Int)
(declare-fun c395215f6_raw_utilization_delta () Int)
(declare-fun c395215f6_target_claimable () Int)
(declare-fun c395215f6_user_claimed_prev_epoch () Int)
(assert
 (= c395215f6_actual_rewards_trust c395215f6_actual_rewards_trust))
(assert
 (= c395215f6_alice_locked_amount_epoch_n c395215f6_alice_locked_amount_epoch_n))
(assert
 (= c395215f6_eligible_prev_epoch c395215f6_eligible_prev_epoch))
(assert
 (= c395215f6_personal_utilization_prior c395215f6_personal_utilization_prior))
(assert
 (= c395215f6_personal_utilization_ratio c395215f6_personal_utilization_ratio))
(assert
 (= c395215f6_raw_utilization_delta c395215f6_raw_utilization_delta))
(assert
 (= c395215f6_target_claimable c395215f6_target_claimable))
(assert
 (= c395215f6_user_claimed_prev_epoch c395215f6_user_claimed_prev_epoch))
(define-fun report_preconditions () Bool (and (= 100000 c395215f6_alice_locked_amount_epoch_n)
     (= 0 c395215f6_eligible_prev_epoch)
     (= 0 c395215f6_user_claimed_prev_epoch)
     (= 0 c395215f6_personal_utilization_prior)
     (= 0 c395215f6_raw_utilization_delta)))
(define-fun report_safety () Bool (=> (and (= 30 c395215f6_personal_utilization_ratio)
         (= 147 c395215f6_actual_rewards_trust))
    (=> (and (= 0 c395215f6_target_claimable)
             (= 0 c395215f6_eligible_prev_epoch))
        (= 100 c395215f6_personal_utilization_ratio))))
(define-fun report_effects () Bool (and (= 30 c395215f6_personal_utilization_ratio)
     (= 147 c395215f6_actual_rewards_trust)
     (= 0 c395215f6_target_claimable)
     (= 0 c395215f6_eligible_prev_epoch)
     (not (= 100 c395215f6_personal_utilization_ratio))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
