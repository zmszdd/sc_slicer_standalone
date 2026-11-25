; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbf067066_owner_can_recover_donated_assets () Bool)
(declare-fun cbf067066_owner_cannot_remove_vaults_observed () Bool)
(declare-fun cbf067066_vault_registered_in_registry () Bool)
(assert
 (= cbf067066_owner_can_recover_donated_assets cbf067066_owner_can_recover_donated_assets))
(assert
 (= cbf067066_owner_cannot_remove_vaults_observed cbf067066_owner_cannot_remove_vaults_observed))
(assert
 (= cbf067066_vault_registered_in_registry cbf067066_vault_registered_in_registry))
(define-fun report_preconditions () Bool cbf067066_vault_registered_in_registry)
(define-fun report_safety () Bool (=> cbf067066_vault_registered_in_registry
    cbf067066_owner_can_recover_donated_assets))
(define-fun report_effects () Bool (and cbf067066_vault_registered_in_registry
     (not cbf067066_owner_can_recover_donated_assets)
     cbf067066_owner_cannot_remove_vaults_observed))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
