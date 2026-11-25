; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cdb9f22f2_total_assets_before_unregister () Int)
(declare-fun cdb9f22f2_unregister_dos_permanent () Bool)
(declare-fun cdb9f22f2_unregister_succeeds () Bool)
(declare-fun cdb9f22f2_vault_asset_balance_before_donation () Int)
(declare-fun cdb9f22f2_vault_deactivated () Bool)
(assert
 (= cdb9f22f2_total_assets_before_unregister cdb9f22f2_total_assets_before_unregister))
(assert
 (= cdb9f22f2_unregister_dos_permanent cdb9f22f2_unregister_dos_permanent))
(assert
 (= cdb9f22f2_unregister_succeeds cdb9f22f2_unregister_succeeds))
(assert
 (= cdb9f22f2_vault_asset_balance_before_donation cdb9f22f2_vault_asset_balance_before_donation))
(assert
 (= cdb9f22f2_vault_deactivated cdb9f22f2_vault_deactivated))
(define-fun report_preconditions () Bool (and (= 0 cdb9f22f2_total_assets_before_unregister)
     cdb9f22f2_vault_deactivated
     (= 0 cdb9f22f2_vault_asset_balance_before_donation)))
(define-fun report_safety () Bool (=> (and (= 0 cdb9f22f2_total_assets_before_unregister)
         cdb9f22f2_vault_deactivated)
    cdb9f22f2_unregister_succeeds))
(define-fun report_effects () Bool (and (= 0 cdb9f22f2_total_assets_before_unregister)
     cdb9f22f2_vault_deactivated
     (not cdb9f22f2_unregister_succeeds)
     cdb9f22f2_unregister_dos_permanent
     cdb9f22f2_unregister_dos_permanent))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
