; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd5a6be6c_owner_can_recover_donated_assets () Bool)
(declare-fun cd5a6be6c_unregister_vault_permanently_blocked () Bool)
(declare-fun cd5a6be6c_vault_registered_in_registry () Bool)
(assert
 (= cd5a6be6c_owner_can_recover_donated_assets cd5a6be6c_owner_can_recover_donated_assets))
(assert
 (= cd5a6be6c_unregister_vault_permanently_blocked cd5a6be6c_unregister_vault_permanently_blocked))
(assert
 (= cd5a6be6c_vault_registered_in_registry cd5a6be6c_vault_registered_in_registry))
(define-fun report_preconditions () Bool cd5a6be6c_vault_registered_in_registry)
(define-fun report_safety () Bool (=> cd5a6be6c_vault_registered_in_registry
    cd5a6be6c_owner_can_recover_donated_assets))
(define-fun report_effects () Bool (and cd5a6be6c_vault_registered_in_registry
     (not cd5a6be6c_owner_can_recover_donated_assets)
     cd5a6be6c_unregister_vault_permanently_blocked
     cd5a6be6c_unregister_vault_permanently_blocked))
