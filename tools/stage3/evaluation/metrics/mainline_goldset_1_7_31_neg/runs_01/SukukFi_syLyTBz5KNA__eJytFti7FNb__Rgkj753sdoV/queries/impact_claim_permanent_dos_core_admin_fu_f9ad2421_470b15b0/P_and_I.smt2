; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cfa1deb2f_donated_assets_recoverable () Bool)
(declare-fun cfa1deb2f_unregister_vault_permanently_blocked () Bool)
(declare-fun cfa1deb2f_vault_balance_zeroed () Bool)
(declare-fun cfa1deb2f_vault_registered () Bool)
(assert
 (= cfa1deb2f_donated_assets_recoverable cfa1deb2f_donated_assets_recoverable))
(assert
 (= cfa1deb2f_unregister_vault_permanently_blocked cfa1deb2f_unregister_vault_permanently_blocked))
(assert
 (= cfa1deb2f_vault_balance_zeroed cfa1deb2f_vault_balance_zeroed))
(assert
 (= cfa1deb2f_vault_registered cfa1deb2f_vault_registered))
(define-fun report_preconditions () Bool (and cfa1deb2f_vault_registered cfa1deb2f_donated_assets_recoverable))
(define-fun report_safety () Bool cfa1deb2f_vault_balance_zeroed)
(define-fun report_effects () Bool (and cfa1deb2f_donated_assets_recoverable
     (not cfa1deb2f_vault_balance_zeroed)
     cfa1deb2f_unregister_vault_permanently_blocked
     cfa1deb2f_unregister_vault_permanently_blocked))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
