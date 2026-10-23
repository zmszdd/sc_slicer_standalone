; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c5116407c_locked_hybr_withdrawable () Bool)
(declare-fun c5116407c_user_holds_ghybr_shares () Bool)
(declare-fun c5116407c_withdraw_completed () Bool)
(assert
 (= c5116407c_locked_hybr_withdrawable c5116407c_locked_hybr_withdrawable))
(assert
 (= c5116407c_user_holds_ghybr_shares c5116407c_user_holds_ghybr_shares))
(assert
 (= c5116407c_withdraw_completed c5116407c_withdraw_completed))
(define-fun report_preconditions () Bool c5116407c_user_holds_ghybr_shares)
(define-fun report_safety () Bool (=> c5116407c_user_holds_ghybr_shares
    (and c5116407c_withdraw_completed c5116407c_locked_hybr_withdrawable)))
(define-fun report_effects () Bool (and c5116407c_user_holds_ghybr_shares
     (not (and c5116407c_withdraw_completed c5116407c_locked_hybr_withdrawable))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
