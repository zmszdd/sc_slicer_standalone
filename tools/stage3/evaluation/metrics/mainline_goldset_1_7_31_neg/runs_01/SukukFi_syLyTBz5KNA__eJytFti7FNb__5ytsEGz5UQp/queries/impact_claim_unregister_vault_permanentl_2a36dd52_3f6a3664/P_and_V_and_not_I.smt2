; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd0cbee22_unregister_blocked_by_dust () Bool)
(declare-fun cd0cbee22_unregister_permanently_blocked () Bool)
(declare-fun cd0cbee22_vault_registered () Bool)
(assert
 (= cd0cbee22_unregister_blocked_by_dust cd0cbee22_unregister_blocked_by_dust))
(assert
 (= cd0cbee22_unregister_permanently_blocked cd0cbee22_unregister_permanently_blocked))
(assert
 (= cd0cbee22_vault_registered cd0cbee22_vault_registered))
(define-fun report_preconditions () Bool cd0cbee22_vault_registered)
(define-fun report_safety () Bool (=> cd0cbee22_vault_registered (not cd0cbee22_unregister_blocked_by_dust)))
(define-fun report_effects () Bool (and cd0cbee22_vault_registered
     cd0cbee22_unregister_blocked_by_dust
     cd0cbee22_unregister_permanently_blocked
     cd0cbee22_unregister_permanently_blocked))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
