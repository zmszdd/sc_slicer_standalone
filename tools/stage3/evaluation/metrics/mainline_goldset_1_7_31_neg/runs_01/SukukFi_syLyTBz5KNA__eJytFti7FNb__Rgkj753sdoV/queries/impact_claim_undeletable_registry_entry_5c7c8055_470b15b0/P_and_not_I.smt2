; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c74b4573a_owner_can_recover_donated_assets () Bool)
(declare-fun c74b4573a_registry_entry_permanent () Bool)
(declare-fun c74b4573a_vault_registered () Bool)
(assert
 (= c74b4573a_owner_can_recover_donated_assets c74b4573a_owner_can_recover_donated_assets))
(assert
 (= c74b4573a_registry_entry_permanent c74b4573a_registry_entry_permanent))
(assert
 (= c74b4573a_vault_registered c74b4573a_vault_registered))
(define-fun report_preconditions () Bool c74b4573a_vault_registered)
(define-fun report_safety () Bool (=> c74b4573a_vault_registered c74b4573a_owner_can_recover_donated_assets))
(define-fun report_effects () Bool (and c74b4573a_vault_registered
     (not c74b4573a_owner_can_recover_donated_assets)
     c74b4573a_registry_entry_permanent
     c74b4573a_registry_entry_permanent))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
