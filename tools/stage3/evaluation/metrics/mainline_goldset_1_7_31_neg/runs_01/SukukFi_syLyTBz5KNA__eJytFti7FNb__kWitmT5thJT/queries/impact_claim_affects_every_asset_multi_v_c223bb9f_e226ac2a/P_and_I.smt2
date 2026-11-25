; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb34f7e0e_dust_donated () Bool)
(declare-fun cb34f7e0e_multi_vault_asset_scope_affected () Bool)
(declare-fun cb34f7e0e_total_assets () Int)
(declare-fun cb34f7e0e_unregister_vault_succeeds () Bool)
(declare-fun cb34f7e0e_vault_asset_balance_before () Int)
(assert
 (= cb34f7e0e_dust_donated cb34f7e0e_dust_donated))
(assert
 (= cb34f7e0e_multi_vault_asset_scope_affected cb34f7e0e_multi_vault_asset_scope_affected))
(assert
 (= cb34f7e0e_total_assets cb34f7e0e_total_assets))
(assert
 (= cb34f7e0e_unregister_vault_succeeds cb34f7e0e_unregister_vault_succeeds))
(assert
 (= cb34f7e0e_vault_asset_balance_before cb34f7e0e_vault_asset_balance_before))
(define-fun report_preconditions () Bool (and (= 0 cb34f7e0e_total_assets)
     (= 0 cb34f7e0e_vault_asset_balance_before)
     cb34f7e0e_dust_donated))
(define-fun report_safety () Bool cb34f7e0e_unregister_vault_succeeds)
(define-fun report_effects () Bool (and cb34f7e0e_dust_donated
     (not cb34f7e0e_unregister_vault_succeeds)
     cb34f7e0e_multi_vault_asset_scope_affected
     cb34f7e0e_multi_vault_asset_scope_affected))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
