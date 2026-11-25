; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7a83389c_donation_received () Bool)
(declare-fun c7a83389c_total_assets_before () Int)
(declare-fun c7a83389c_unregister_vault_dos_permanent () Bool)
(declare-fun c7a83389c_unregister_vault_succeeds () Bool)
(declare-fun c7a83389c_vault_asset_balance_before () Int)
(assert
 (= c7a83389c_donation_received c7a83389c_donation_received))
(assert
 (= c7a83389c_total_assets_before c7a83389c_total_assets_before))
(assert
 (= c7a83389c_unregister_vault_dos_permanent c7a83389c_unregister_vault_dos_permanent))
(assert
 (= c7a83389c_unregister_vault_succeeds c7a83389c_unregister_vault_succeeds))
(assert
 (= c7a83389c_vault_asset_balance_before c7a83389c_vault_asset_balance_before))
(define-fun report_preconditions () Bool (and (= 0 c7a83389c_total_assets_before)
     (= 0 c7a83389c_vault_asset_balance_before)
     c7a83389c_donation_received))
(define-fun report_safety () Bool c7a83389c_unregister_vault_succeeds)
(define-fun report_effects () Bool (and c7a83389c_donation_received
     (not c7a83389c_unregister_vault_succeeds)
     c7a83389c_unregister_vault_dos_permanent
     c7a83389c_donation_received
     c7a83389c_unregister_vault_dos_permanent))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
