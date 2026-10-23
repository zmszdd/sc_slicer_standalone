; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ccac4ee4e_user_holds_ghybr_shares () Bool)
(declare-fun ccac4ee4e_withdrawal_completed () Bool)
(declare-fun ccac4ee4e_withdrawal_fails () Bool)
(assert
 (= ccac4ee4e_user_holds_ghybr_shares ccac4ee4e_user_holds_ghybr_shares))
(assert
 (= ccac4ee4e_withdrawal_completed ccac4ee4e_withdrawal_completed))
(assert
 (= ccac4ee4e_withdrawal_fails ccac4ee4e_withdrawal_fails))
(define-fun report_preconditions () Bool ccac4ee4e_user_holds_ghybr_shares)
(define-fun report_safety () Bool (=> ccac4ee4e_user_holds_ghybr_shares
    (and ccac4ee4e_withdrawal_completed (not ccac4ee4e_withdrawal_fails))))
(define-fun report_effects () Bool (and ccac4ee4e_user_holds_ghybr_shares
     (not (and ccac4ee4e_withdrawal_completed (not ccac4ee4e_withdrawal_fails)))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
