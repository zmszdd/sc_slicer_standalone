; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c97374895_total_assets_before () Int)
(declare-fun c97374895_unregister_reverts () Bool)
(declare-fun c97374895_vault_asset_balance_after () Int)
(declare-fun c97374895_vault_asset_balance_before () Int)
(declare-fun c97374895_zero_amount () Int)
(assert
 (= c97374895_total_assets_before c97374895_total_assets_before))
(assert
 (= c97374895_unregister_reverts c97374895_unregister_reverts))
(assert
 (= c97374895_vault_asset_balance_after c97374895_vault_asset_balance_after))
(assert
 (= c97374895_vault_asset_balance_before c97374895_vault_asset_balance_before))
(assert
 (= c97374895_zero_amount c97374895_zero_amount))
(define-fun report_preconditions () Bool (and (= c97374895_total_assets_before c97374895_zero_amount)
     (= c97374895_vault_asset_balance_before c97374895_zero_amount)))
(define-fun report_safety () Bool (=> (= c97374895_total_assets_before c97374895_zero_amount)
    (not c97374895_unregister_reverts)))
(define-fun report_effects () Bool (and (= c97374895_total_assets_before c97374895_zero_amount)
     c97374895_unregister_reverts
     (> c97374895_vault_asset_balance_after c97374895_zero_amount)
     c97374895_unregister_reverts))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
