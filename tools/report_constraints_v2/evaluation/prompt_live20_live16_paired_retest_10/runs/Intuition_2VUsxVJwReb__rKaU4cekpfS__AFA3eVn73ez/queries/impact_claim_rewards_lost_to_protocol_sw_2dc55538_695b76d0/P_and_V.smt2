; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c898274bd_alice_locked_amount () Int)
(declare-fun c898274bd_eligible_prev_epoch () Int)
(declare-fun c898274bd_intended_utilization_ratio () Int)
(declare-fun c898274bd_personal_utilization () Int)
(declare-fun c898274bd_swept_reward_amount () Int)
(declare-fun c898274bd_target_claimable () Int)
(declare-fun c898274bd_user_claimed_prev_epoch () Int)
(assert
 (= c898274bd_alice_locked_amount c898274bd_alice_locked_amount))
(assert
 (= c898274bd_eligible_prev_epoch c898274bd_eligible_prev_epoch))
(assert
 (= c898274bd_intended_utilization_ratio c898274bd_intended_utilization_ratio))
(assert
 (= c898274bd_personal_utilization c898274bd_personal_utilization))
(assert
 (= c898274bd_swept_reward_amount c898274bd_swept_reward_amount))
(assert
 (= c898274bd_target_claimable c898274bd_target_claimable))
(assert
 (= c898274bd_user_claimed_prev_epoch c898274bd_user_claimed_prev_epoch))
(define-fun report_preconditions () Bool (and (= 100000 c898274bd_alice_locked_amount)
     (= 0 c898274bd_eligible_prev_epoch)
     (= 0 c898274bd_user_claimed_prev_epoch)
     (= 0 c898274bd_personal_utilization)))
(define-fun report_safety () Bool (=> (and (= 0 c898274bd_target_claimable) (= 0 c898274bd_eligible_prev_epoch))
    (= 100 c898274bd_intended_utilization_ratio)))
(define-fun report_effects () Bool (= 343 c898274bd_swept_reward_amount))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
