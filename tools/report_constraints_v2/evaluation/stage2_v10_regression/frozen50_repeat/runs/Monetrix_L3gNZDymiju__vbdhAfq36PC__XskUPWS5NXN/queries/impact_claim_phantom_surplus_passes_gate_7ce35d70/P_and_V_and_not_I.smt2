; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd7fded92_auto_borrow_triggered () Bool)
(declare-fun cd7fded92_portfolio_margin_activated () Bool)
(declare-fun cd7fded92_settle_accepts_unbacked_yield () Bool)
(declare-fun cd7fded92_vault_holds_hl_position () Bool)
(assert
 (= cd7fded92_auto_borrow_triggered cd7fded92_auto_borrow_triggered))
(assert
 (= cd7fded92_portfolio_margin_activated cd7fded92_portfolio_margin_activated))
(assert
 (= cd7fded92_settle_accepts_unbacked_yield cd7fded92_settle_accepts_unbacked_yield))
(assert
 (= cd7fded92_vault_holds_hl_position cd7fded92_vault_holds_hl_position))
(define-fun report_preconditions () Bool (and cd7fded92_portfolio_margin_activated
     cd7fded92_vault_holds_hl_position
     cd7fded92_auto_borrow_triggered))
(define-fun report_safety () Bool (=> (and cd7fded92_portfolio_margin_activated
         cd7fded92_vault_holds_hl_position
         cd7fded92_auto_borrow_triggered)
    (not cd7fded92_settle_accepts_unbacked_yield)))
(define-fun report_effects () Bool (and cd7fded92_portfolio_margin_activated
     cd7fded92_vault_holds_hl_position
     cd7fded92_auto_borrow_triggered
     (not (not cd7fded92_settle_accepts_unbacked_yield))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
