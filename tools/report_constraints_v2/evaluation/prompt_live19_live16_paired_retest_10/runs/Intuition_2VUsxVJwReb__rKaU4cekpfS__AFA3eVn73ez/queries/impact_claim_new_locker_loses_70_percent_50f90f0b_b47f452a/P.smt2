; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd877aa8a_alice_locked_amount_epoch_n () Int)
(declare-fun cd877aa8a_eligible_prev_epoch () Int)
(declare-fun cd877aa8a_personal_utilization () Int)
(declare-fun cd877aa8a_personal_utilization_ratio_observed () Int)
(declare-fun cd877aa8a_raw_utilization_delta () Int)
(declare-fun cd877aa8a_rewards_lost_fraction () Int)
(declare-fun cd877aa8a_target_claimable_prev_epoch () Int)
(declare-fun cd877aa8a_user_claimed_rewards_prev_epoch () Int)
(assert
 (= cd877aa8a_alice_locked_amount_epoch_n cd877aa8a_alice_locked_amount_epoch_n))
(assert
 (= cd877aa8a_eligible_prev_epoch cd877aa8a_eligible_prev_epoch))
(assert
 (= cd877aa8a_personal_utilization cd877aa8a_personal_utilization))
(assert
 (= cd877aa8a_personal_utilization_ratio_observed cd877aa8a_personal_utilization_ratio_observed))
(assert
 (= cd877aa8a_raw_utilization_delta cd877aa8a_raw_utilization_delta))
(assert
 (= cd877aa8a_rewards_lost_fraction cd877aa8a_rewards_lost_fraction))
(assert
 (= cd877aa8a_target_claimable_prev_epoch cd877aa8a_target_claimable_prev_epoch))
(assert
 (= cd877aa8a_user_claimed_rewards_prev_epoch cd877aa8a_user_claimed_rewards_prev_epoch))
(define-fun report_preconditions () Bool (and (= 100000 cd877aa8a_alice_locked_amount_epoch_n)
     (= 0 cd877aa8a_eligible_prev_epoch)
     (= 0 cd877aa8a_user_claimed_rewards_prev_epoch)
     (= 0 cd877aa8a_personal_utilization)
     (= 0 cd877aa8a_raw_utilization_delta)))
(define-fun report_safety () Bool (=> (and (= 70 cd877aa8a_rewards_lost_fraction)
         (= 30 cd877aa8a_personal_utilization_ratio_observed))
    (=> (and (= 0 cd877aa8a_target_claimable_prev_epoch)
             (= 0 cd877aa8a_eligible_prev_epoch))
        (= 100 cd877aa8a_personal_utilization_ratio_observed))))
(define-fun report_effects () Bool (and (= 70 cd877aa8a_rewards_lost_fraction)
     (= 30 cd877aa8a_personal_utilization_ratio_observed)
     (= 0 cd877aa8a_target_claimable_prev_epoch)
     (= 0 cd877aa8a_eligible_prev_epoch)
     (not (= 100 cd877aa8a_personal_utilization_ratio_observed))))
(assert report_preconditions)
(check-sat)
(get-model)
