; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cfb330798_core_functionality_dos_occurred () Bool)
(declare-fun cfb330798_owner_initiates_unregister_occurred () Bool)
(declare-fun cfb330798_unregister_completed () Bool)
(declare-fun cfb330798_vault_asset_balance () Int)
(declare-fun cfb330798_zero () Int)
(assert
 (= cfb330798_core_functionality_dos_occurred cfb330798_core_functionality_dos_occurred))
(assert
 (= cfb330798_owner_initiates_unregister_occurred cfb330798_owner_initiates_unregister_occurred))
(assert
 (= cfb330798_unregister_completed cfb330798_unregister_completed))
(assert
 (= cfb330798_vault_asset_balance cfb330798_vault_asset_balance))
(assert
 (= cfb330798_zero cfb330798_zero))
(define-fun report_preconditions () Bool (and cfb330798_owner_initiates_unregister_occurred
     (= cfb330798_vault_asset_balance cfb330798_zero)))
(define-fun report_safety () Bool (=> (and cfb330798_owner_initiates_unregister_occurred
         (= cfb330798_vault_asset_balance cfb330798_zero))
    (and cfb330798_unregister_completed
         (not cfb330798_core_functionality_dos_occurred))))
(define-fun report_effects () Bool (and cfb330798_owner_initiates_unregister_occurred
     (= cfb330798_vault_asset_balance cfb330798_zero)
     (not (and cfb330798_unregister_completed
               (not cfb330798_core_functionality_dos_occurred)))))
(assert report_preconditions)
(check-sat)
(get-model)
