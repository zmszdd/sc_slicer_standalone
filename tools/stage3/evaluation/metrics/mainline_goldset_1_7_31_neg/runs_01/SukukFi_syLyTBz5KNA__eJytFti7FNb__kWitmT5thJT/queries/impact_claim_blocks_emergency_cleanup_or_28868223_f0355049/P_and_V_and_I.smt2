; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c910a7cf4_emergency_cleanup_blocked () Bool)
(declare-fun c910a7cf4_total_assets () Int)
(declare-fun c910a7cf4_unregister_succeeds () Bool)
(declare-fun c910a7cf4_vault_asset_balance () Int)
(declare-fun c910a7cf4_vault_deactivated () Bool)
(assert
 (= c910a7cf4_emergency_cleanup_blocked c910a7cf4_emergency_cleanup_blocked))
(assert
 (= c910a7cf4_total_assets c910a7cf4_total_assets))
(assert
 (= c910a7cf4_unregister_succeeds c910a7cf4_unregister_succeeds))
(assert
 (= c910a7cf4_vault_asset_balance c910a7cf4_vault_asset_balance))
(assert
 (= c910a7cf4_vault_deactivated c910a7cf4_vault_deactivated))
(define-fun report_preconditions () Bool (and (= 0 c910a7cf4_total_assets)
     c910a7cf4_vault_deactivated
     (= 0 c910a7cf4_vault_asset_balance)))
(define-fun report_safety () Bool (=> (and (= 0 c910a7cf4_total_assets) c910a7cf4_vault_deactivated)
    c910a7cf4_unregister_succeeds))
(define-fun report_effects () Bool (and (= 0 c910a7cf4_total_assets)
     c910a7cf4_vault_deactivated
     (not c910a7cf4_unregister_succeeds)
     c910a7cf4_emergency_cleanup_blocked))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
