; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c38026f64_all_assets_affected () Bool)
(declare-fun c38026f64_total_assets () Int)
(declare-fun c38026f64_unregister_succeeds () Bool)
(declare-fun c38026f64_vault_asset_balance_before () Int)
(declare-fun c38026f64_vault_deactivated () Bool)
(assert
 (= c38026f64_all_assets_affected c38026f64_all_assets_affected))
(assert
 (= c38026f64_total_assets c38026f64_total_assets))
(assert
 (= c38026f64_unregister_succeeds c38026f64_unregister_succeeds))
(assert
 (= c38026f64_vault_asset_balance_before c38026f64_vault_asset_balance_before))
(assert
 (= c38026f64_vault_deactivated c38026f64_vault_deactivated))
(define-fun report_preconditions () Bool (and (= 0 c38026f64_total_assets)
     c38026f64_vault_deactivated
     (= 0 c38026f64_vault_asset_balance_before)))
(define-fun report_safety () Bool (=> (and (= 0 c38026f64_total_assets) c38026f64_vault_deactivated)
    c38026f64_unregister_succeeds))
(define-fun report_effects () Bool (and (= 0 c38026f64_total_assets)
     c38026f64_vault_deactivated
     (not c38026f64_unregister_succeeds)
     c38026f64_all_assets_affected
     c38026f64_all_assets_affected))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
