; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9a78dadd_total_assets_before () Int)
(declare-fun c9a78dadd_unregister_reverts () Bool)
(declare-fun c9a78dadd_vault_asset_balance_after () Int)
(declare-fun c9a78dadd_vault_asset_balance_before () Int)
(declare-fun c9a78dadd_zero () Int)
(assert
 (= c9a78dadd_total_assets_before c9a78dadd_total_assets_before))
(assert
 (= c9a78dadd_unregister_reverts c9a78dadd_unregister_reverts))
(assert
 (= c9a78dadd_vault_asset_balance_after c9a78dadd_vault_asset_balance_after))
(assert
 (= c9a78dadd_vault_asset_balance_before c9a78dadd_vault_asset_balance_before))
(assert
 (= c9a78dadd_zero c9a78dadd_zero))
(define-fun report_preconditions () Bool (and (= c9a78dadd_total_assets_before c9a78dadd_zero)
     (= c9a78dadd_vault_asset_balance_before c9a78dadd_zero)))
(define-fun report_safety () Bool (=> (> c9a78dadd_vault_asset_balance_after c9a78dadd_zero)
    (not c9a78dadd_unregister_reverts)))
(define-fun report_effects () Bool (and (and (> c9a78dadd_vault_asset_balance_after c9a78dadd_zero)
          c9a78dadd_unregister_reverts)
     (and (> c9a78dadd_vault_asset_balance_after c9a78dadd_zero)
          c9a78dadd_unregister_reverts)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
