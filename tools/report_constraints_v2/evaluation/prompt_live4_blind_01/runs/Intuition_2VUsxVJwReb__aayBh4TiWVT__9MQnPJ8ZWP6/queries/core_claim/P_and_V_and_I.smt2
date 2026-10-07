; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun user_active_prev_epoch () Bool)
(declare-fun user_inactive_current_epoch () Bool)
(declare-fun eligible_rewards () Int)
(declare-fun received_rewards () Int)
(declare-fun floor_numerator () Int)
(declare-fun floor_denominator () Int)
(assert
 (= user_active_prev_epoch user_active_prev_epoch))
(assert
 (= user_inactive_current_epoch user_inactive_current_epoch))
(assert
 (= eligible_rewards eligible_rewards))
(assert
 (= received_rewards received_rewards))
(assert
 (= floor_numerator floor_numerator))
(assert
 (= floor_denominator floor_denominator))
(define-fun report_preconditions () Bool (and user_active_prev_epoch user_inactive_current_epoch))
(define-fun report_safety () Bool (=> (and user_active_prev_epoch user_inactive_current_epoch)
    (> (* received_rewards floor_denominator)
       (* eligible_rewards floor_numerator))))
(define-fun report_effects () Bool (and user_active_prev_epoch
     user_inactive_current_epoch
     (not (> (* received_rewards floor_denominator)
             (* eligible_rewards floor_numerator)))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
