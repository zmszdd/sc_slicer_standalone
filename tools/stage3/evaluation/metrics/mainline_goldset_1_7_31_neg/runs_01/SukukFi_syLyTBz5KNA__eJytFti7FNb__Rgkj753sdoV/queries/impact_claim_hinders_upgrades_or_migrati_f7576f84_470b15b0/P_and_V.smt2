; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c507bb979_owner_can_recover_donated_assets () Bool)
(declare-fun c507bb979_unregister_vault_proceeds () Bool)
(declare-fun c507bb979_upgrades_or_migration_hindered () Bool)
(declare-fun c507bb979_vault_registered () Bool)
(assert
 (= c507bb979_owner_can_recover_donated_assets c507bb979_owner_can_recover_donated_assets))
(assert
 (= c507bb979_unregister_vault_proceeds c507bb979_unregister_vault_proceeds))
(assert
 (= c507bb979_upgrades_or_migration_hindered c507bb979_upgrades_or_migration_hindered))
(assert
 (= c507bb979_vault_registered c507bb979_vault_registered))
(define-fun report_preconditions () Bool c507bb979_vault_registered)
(define-fun report_safety () Bool (=> c507bb979_vault_registered
    (and c507bb979_owner_can_recover_donated_assets
         c507bb979_unregister_vault_proceeds)))
(define-fun report_effects () Bool (and c507bb979_vault_registered
     (not (and c507bb979_owner_can_recover_donated_assets
               c507bb979_unregister_vault_proceeds))
     c507bb979_upgrades_or_migration_hindered))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
