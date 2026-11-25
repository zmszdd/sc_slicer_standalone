; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cce49b011_no_outstanding_shares () Bool)
(declare-fun cce49b011_unregister_checks_outstanding_shares_not_asset_balance () Bool)
(declare-fun cce49b011_upgrade_or_migration_hindered () Bool)
(declare-fun cce49b011_vault_registered () Bool)
(assert
 (= cce49b011_no_outstanding_shares cce49b011_no_outstanding_shares))
(assert
 (= cce49b011_unregister_checks_outstanding_shares_not_asset_balance cce49b011_unregister_checks_outstanding_shares_not_asset_balance))
(assert
 (= cce49b011_upgrade_or_migration_hindered cce49b011_upgrade_or_migration_hindered))
(assert
 (= cce49b011_vault_registered cce49b011_vault_registered))
(define-fun report_preconditions () Bool (and cce49b011_vault_registered cce49b011_no_outstanding_shares))
(define-fun report_safety () Bool cce49b011_unregister_checks_outstanding_shares_not_asset_balance)
(define-fun report_effects () Bool (and cce49b011_no_outstanding_shares
     (not cce49b011_unregister_checks_outstanding_shares_not_asset_balance)
     cce49b011_upgrade_or_migration_hindered))
(assert report_preconditions)
(check-sat)
(get-model)
