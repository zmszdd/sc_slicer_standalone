; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3115cb77_decommissioning_blocked () Bool)
(declare-fun c3115cb77_unregister_vault_succeeds () Bool)
(declare-fun c3115cb77_vault_asset_balance_before_donation () Int)
(declare-fun c3115cb77_vault_total_assets () Int)
(assert
 (= c3115cb77_decommissioning_blocked c3115cb77_decommissioning_blocked))
(assert
 (= c3115cb77_unregister_vault_succeeds c3115cb77_unregister_vault_succeeds))
(assert
 (= c3115cb77_vault_asset_balance_before_donation c3115cb77_vault_asset_balance_before_donation))
(assert
 (= c3115cb77_vault_total_assets c3115cb77_vault_total_assets))
(define-fun report_preconditions () Bool (and (= 0 c3115cb77_vault_total_assets)
     (= 0 c3115cb77_vault_asset_balance_before_donation)))
(define-fun report_safety () Bool (=> (= 0 c3115cb77_vault_total_assets) c3115cb77_unregister_vault_succeeds))
(define-fun report_effects () Bool (and (= 0 c3115cb77_vault_total_assets)
     (not c3115cb77_unregister_vault_succeeds)
     c3115cb77_decommissioning_blocked))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
