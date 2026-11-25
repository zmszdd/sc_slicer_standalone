; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd91f55d9_migration_blocked () Bool)
(declare-fun cd91f55d9_total_assets () Int)
(declare-fun cd91f55d9_unregister_succeeds () Bool)
(declare-fun cd91f55d9_vault_asset_balance () Int)
(assert
 (= cd91f55d9_migration_blocked cd91f55d9_migration_blocked))
(assert
 (= cd91f55d9_total_assets cd91f55d9_total_assets))
(assert
 (= cd91f55d9_unregister_succeeds cd91f55d9_unregister_succeeds))
(assert
 (= cd91f55d9_vault_asset_balance cd91f55d9_vault_asset_balance))
(define-fun report_preconditions () Bool (and (= 0 cd91f55d9_total_assets) (= 0 cd91f55d9_vault_asset_balance)))
(define-fun report_safety () Bool (=> (= 0 cd91f55d9_total_assets) cd91f55d9_unregister_succeeds))
(define-fun report_effects () Bool (and (= 0 cd91f55d9_total_assets)
     (not cd91f55d9_unregister_succeeds)
     cd91f55d9_migration_blocked))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
