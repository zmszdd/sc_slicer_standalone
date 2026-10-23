; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4c163fee_user_holds_shares () Bool)
(declare-fun c4c163fee_withdraw_completed () Bool)
(assert
 (= c4c163fee_user_holds_shares c4c163fee_user_holds_shares))
(assert
 (= c4c163fee_withdraw_completed c4c163fee_withdraw_completed))
(define-fun report_preconditions () Bool c4c163fee_user_holds_shares)
(define-fun report_safety () Bool (=> c4c163fee_user_holds_shares c4c163fee_withdraw_completed))
(define-fun report_effects () Bool (and c4c163fee_user_holds_shares (not c4c163fee_withdraw_completed)))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
