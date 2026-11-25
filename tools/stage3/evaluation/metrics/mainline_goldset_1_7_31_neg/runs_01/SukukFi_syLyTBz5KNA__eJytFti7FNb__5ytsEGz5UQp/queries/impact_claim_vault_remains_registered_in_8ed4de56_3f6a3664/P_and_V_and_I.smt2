; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cedbfaf1e_unregister_blocked_by_excess_underlying () Bool)
(declare-fun cedbfaf1e_vault_is_registered () Bool)
(declare-fun cedbfaf1e_vault_registered_indefinitely () Bool)
(assert
 (= cedbfaf1e_unregister_blocked_by_excess_underlying cedbfaf1e_unregister_blocked_by_excess_underlying))
(assert
 (= cedbfaf1e_vault_is_registered cedbfaf1e_vault_is_registered))
(assert
 (= cedbfaf1e_vault_registered_indefinitely cedbfaf1e_vault_registered_indefinitely))
(define-fun report_preconditions () Bool cedbfaf1e_vault_is_registered)
(define-fun report_safety () Bool (=> cedbfaf1e_vault_is_registered
    (not cedbfaf1e_unregister_blocked_by_excess_underlying)))
(define-fun report_effects () Bool (and cedbfaf1e_vault_is_registered
     cedbfaf1e_unregister_blocked_by_excess_underlying
     cedbfaf1e_vault_registered_indefinitely
     cedbfaf1e_vault_registered_indefinitely))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
