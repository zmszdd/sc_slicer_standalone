; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cdc51a227_user_holds_ghybr_shares () Bool)
(declare-fun cdc51a227_user_unable_to_exit () Bool)
(declare-fun cdc51a227_withdrawal_completed () Bool)
(assert
 (= cdc51a227_user_holds_ghybr_shares cdc51a227_user_holds_ghybr_shares))
(assert
 (= cdc51a227_user_unable_to_exit cdc51a227_user_unable_to_exit))
(assert
 (= cdc51a227_withdrawal_completed cdc51a227_withdrawal_completed))
(define-fun report_preconditions () Bool cdc51a227_user_holds_ghybr_shares)
(define-fun report_safety () Bool (=> cdc51a227_user_holds_ghybr_shares
    (and cdc51a227_withdrawal_completed (not cdc51a227_user_unable_to_exit))))
(define-fun report_effects () Bool (and cdc51a227_user_holds_ghybr_shares
     (not (and cdc51a227_withdrawal_completed
               (not cdc51a227_user_unable_to_exit)))))
