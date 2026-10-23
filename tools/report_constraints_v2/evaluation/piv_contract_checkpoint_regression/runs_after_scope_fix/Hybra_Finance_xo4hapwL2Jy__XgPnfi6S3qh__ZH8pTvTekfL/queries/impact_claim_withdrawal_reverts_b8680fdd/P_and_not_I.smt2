; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cee45b219_user_holds_ghybr_shares () Bool)
(declare-fun cee45b219_withdrawal_reverts_observed () Bool)
(assert
 (= cee45b219_user_holds_ghybr_shares cee45b219_user_holds_ghybr_shares))
(assert
 (= cee45b219_withdrawal_reverts_observed cee45b219_withdrawal_reverts_observed))
(define-fun report_preconditions () Bool cee45b219_user_holds_ghybr_shares)
(define-fun report_safety () Bool (=> cee45b219_user_holds_ghybr_shares
    (not cee45b219_withdrawal_reverts_observed)))
(define-fun report_effects () Bool (and cee45b219_user_holds_ghybr_shares
     (not (not cee45b219_withdrawal_reverts_observed))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
