; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3546c068_user_holds_shares () Bool)
(declare-fun c3546c068_withdrawal_completed () Bool)
(assert
 (= c3546c068_user_holds_shares c3546c068_user_holds_shares))
(assert
 (= c3546c068_withdrawal_completed c3546c068_withdrawal_completed))
(define-fun report_preconditions () Bool c3546c068_user_holds_shares)
(define-fun report_safety () Bool (=> c3546c068_user_holds_shares c3546c068_withdrawal_completed))
(define-fun report_effects () Bool (and c3546c068_user_holds_shares (not c3546c068_withdrawal_completed)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
