; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c859fa0e1_decommissioning_blocked () Bool)
(declare-fun c859fa0e1_total_assets () Int)
(declare-fun c859fa0e1_unregister_succeeds () Bool)
(declare-fun c859fa0e1_vault_asset_balance () Int)
(declare-fun c859fa0e1_vault_deactivated () Bool)
(assert
 (= c859fa0e1_decommissioning_blocked c859fa0e1_decommissioning_blocked))
(assert
 (= c859fa0e1_total_assets c859fa0e1_total_assets))
(assert
 (= c859fa0e1_unregister_succeeds c859fa0e1_unregister_succeeds))
(assert
 (= c859fa0e1_vault_asset_balance c859fa0e1_vault_asset_balance))
(assert
 (= c859fa0e1_vault_deactivated c859fa0e1_vault_deactivated))
(define-fun report_preconditions () Bool (and (= 0 c859fa0e1_total_assets)
     c859fa0e1_vault_deactivated
     (= 0 c859fa0e1_vault_asset_balance)))
(define-fun report_safety () Bool (=> (and (= 0 c859fa0e1_total_assets) c859fa0e1_vault_deactivated)
    c859fa0e1_unregister_succeeds))
(define-fun report_effects () Bool (and (= 0 c859fa0e1_total_assets)
     c859fa0e1_vault_deactivated
     (not c859fa0e1_unregister_succeeds)
     c859fa0e1_decommissioning_blocked))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
