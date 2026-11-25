; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c5c97e369_registry_permanently_locked () Bool)
(declare-fun c5c97e369_vault_registered () Bool)
(assert
 (= c5c97e369_registry_permanently_locked c5c97e369_registry_permanently_locked))
(assert
 (= c5c97e369_vault_registered c5c97e369_vault_registered))
(define-fun report_preconditions () Bool c5c97e369_vault_registered)
(define-fun report_safety () Bool (=> c5c97e369_vault_registered (not c5c97e369_registry_permanently_locked)))
(define-fun report_effects () Bool (and c5c97e369_vault_registered
     c5c97e369_registry_permanently_locked
     c5c97e369_registry_permanently_locked
     c5c97e369_registry_permanently_locked))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
