; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6c2686f2_unregister_dos_permanent () Bool)
(declare-fun c6c2686f2_unregister_succeeds () Bool)
(declare-fun c6c2686f2_vault_asset_balance_before () Int)
(declare-fun c6c2686f2_vault_total_assets () Int)
(assert
 (= c6c2686f2_unregister_dos_permanent c6c2686f2_unregister_dos_permanent))
(assert
 (= c6c2686f2_unregister_succeeds c6c2686f2_unregister_succeeds))
(assert
 (= c6c2686f2_vault_asset_balance_before c6c2686f2_vault_asset_balance_before))
(assert
 (= c6c2686f2_vault_total_assets c6c2686f2_vault_total_assets))
(define-fun report_preconditions () Bool (and (= 0 c6c2686f2_vault_total_assets)
     (= 0 c6c2686f2_vault_asset_balance_before)))
(define-fun report_safety () Bool (=> (= 0 c6c2686f2_vault_total_assets) c6c2686f2_unregister_succeeds))
(define-fun report_effects () Bool (and (= 0 c6c2686f2_vault_total_assets)
     (not c6c2686f2_unregister_succeeds)
     c6c2686f2_unregister_dos_permanent
     c6c2686f2_unregister_dos_permanent))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
