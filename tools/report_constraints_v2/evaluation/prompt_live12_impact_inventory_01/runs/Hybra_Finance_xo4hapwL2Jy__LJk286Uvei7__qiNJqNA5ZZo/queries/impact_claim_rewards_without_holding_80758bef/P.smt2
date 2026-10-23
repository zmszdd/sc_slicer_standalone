; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c277b665c_maturity_time_before_deposit () Int)
(declare-fun c277b665c_rewards_earned_without_lock () Bool)
(assert
 (= c277b665c_maturity_time_before_deposit c277b665c_maturity_time_before_deposit))
(assert
 (= c277b665c_rewards_earned_without_lock c277b665c_rewards_earned_without_lock))
(define-fun report_preconditions () Bool (= 0 c277b665c_maturity_time_before_deposit))
(define-fun report_safety () Bool (=> (= 0 c277b665c_maturity_time_before_deposit)
    (not c277b665c_rewards_earned_without_lock)))
(define-fun report_effects () Bool (and (= 0 c277b665c_maturity_time_before_deposit)
     (not (not c277b665c_rewards_earned_without_lock))))
(assert report_preconditions)
(check-sat)
(get-model)
