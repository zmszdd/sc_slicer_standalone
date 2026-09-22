; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun investment_token_configured () Bool)
(declare-fun vault_registered () Bool)
(declare-fun max_allowance_granted () Bool)
(declare-fun unregister_executed () Bool)
(declare-fun allowance () Int)
(assert
 (= investment_token_configured investment_token_configured))
(assert
 (= vault_registered vault_registered))
(assert
 (= max_allowance_granted max_allowance_granted))
(assert
 (= unregister_executed unregister_executed))
(assert
 (= allowance allowance))
(define-fun report_preconditions () Bool (and investment_token_configured vault_registered max_allowance_granted))
(define-fun report_safety () Bool (=> unregister_executed (= 0 allowance)))
(define-fun report_effects () Bool (and unregister_executed (not (= 0 allowance))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
