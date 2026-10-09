; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun vault_registered () Bool)
(declare-fun vault_balance () Int)
(declare-fun unregister_blocked () Bool)
(assert
 (= vault_registered vault_registered))
(assert
 (= vault_balance vault_balance))
(assert
 (= unregister_blocked unregister_blocked))
(define-fun report_preconditions () Bool (and vault_registered (= 0 vault_balance)))
(define-fun report_safety () Bool (=> (and vault_registered (= 0 vault_balance)) (not unregister_blocked)))
(define-fun report_effects () Bool (and vault_registered (= 0 vault_balance) unregister_blocked))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
