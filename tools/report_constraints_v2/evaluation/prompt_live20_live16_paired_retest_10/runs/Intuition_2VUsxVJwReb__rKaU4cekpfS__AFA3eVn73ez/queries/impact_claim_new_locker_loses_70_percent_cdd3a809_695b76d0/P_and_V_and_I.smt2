; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3b4b969e_alice_locked_amount () Int)
(declare-fun c3b4b969e_eligible_prev_epoch () Int)
(declare-fun c3b4b969e_first_epoch_rewards_lost_percent () Int)
(declare-fun c3b4b969e_personal_utilization_ratio () Int)
(declare-fun c3b4b969e_user_claimed_rewards_prev_epoch () Int)
(assert
 (= c3b4b969e_alice_locked_amount c3b4b969e_alice_locked_amount))
(assert
 (= c3b4b969e_eligible_prev_epoch c3b4b969e_eligible_prev_epoch))
(assert
 (= c3b4b969e_first_epoch_rewards_lost_percent c3b4b969e_first_epoch_rewards_lost_percent))
(assert
 (= c3b4b969e_personal_utilization_ratio c3b4b969e_personal_utilization_ratio))
(assert
 (= c3b4b969e_user_claimed_rewards_prev_epoch c3b4b969e_user_claimed_rewards_prev_epoch))
(define-fun report_preconditions () Bool (and (= 100000 c3b4b969e_alice_locked_amount)
     (= 0 c3b4b969e_eligible_prev_epoch)
     (= 0 c3b4b969e_user_claimed_rewards_prev_epoch)
     (= 0 c3b4b969e_personal_utilization_ratio)))
(define-fun report_safety () Bool (=> (and (= 0 c3b4b969e_eligible_prev_epoch)
         (= 0 c3b4b969e_user_claimed_rewards_prev_epoch))
    (= 100 c3b4b969e_personal_utilization_ratio)))
(define-fun report_effects () Bool (and (= 70 c3b4b969e_first_epoch_rewards_lost_percent)
     (= 0 c3b4b969e_personal_utilization_ratio)
     (= 70 c3b4b969e_first_epoch_rewards_lost_percent)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
