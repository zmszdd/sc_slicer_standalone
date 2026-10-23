; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun builder_wallet_holds_fees_occurred () Bool)
(declare-fun builder_admin_overwritten () Bool)
(declare-fun fees_drained () Bool)
(assert
 (= builder_wallet_holds_fees_occurred builder_wallet_holds_fees_occurred))
(assert
 (= builder_admin_overwritten builder_admin_overwritten))
(assert
 (= fees_drained fees_drained))
(define-fun report_preconditions () Bool builder_wallet_holds_fees_occurred)
(define-fun report_safety () Bool (=> (and builder_wallet_holds_fees_occurred builder_admin_overwritten)
    (not fees_drained)))
(define-fun report_effects () Bool (and builder_wallet_holds_fees_occurred
     builder_admin_overwritten
     (not (not fees_drained))))
