; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c200a3a8d_owner_initiates_unregister () Bool)
(declare-fun c200a3a8d_unregister_completed () Bool)
(declare-fun c200a3a8d_vault_asset_balance () Int)
(assert
 (= c200a3a8d_owner_initiates_unregister c200a3a8d_owner_initiates_unregister))
(assert
 (= c200a3a8d_unregister_completed c200a3a8d_unregister_completed))
(assert
 (= c200a3a8d_vault_asset_balance c200a3a8d_vault_asset_balance))
(define-fun report_preconditions () Bool (and c200a3a8d_owner_initiates_unregister (= 0 c200a3a8d_vault_asset_balance)))
(define-fun report_safety () Bool (=> (and c200a3a8d_owner_initiates_unregister
         (= 0 c200a3a8d_vault_asset_balance))
    c200a3a8d_unregister_completed))
(define-fun report_effects () Bool (and c200a3a8d_owner_initiates_unregister
     (= 0 c200a3a8d_vault_asset_balance)
     (not c200a3a8d_unregister_completed)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
