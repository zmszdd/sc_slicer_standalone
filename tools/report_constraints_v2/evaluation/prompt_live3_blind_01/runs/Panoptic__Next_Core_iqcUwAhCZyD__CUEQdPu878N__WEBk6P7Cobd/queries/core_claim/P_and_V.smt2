; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun wallet_initialized () Bool)
(declare-fun init_callable () Bool)
(declare-fun attacker_is_admin_after () Bool)
(assert
 (= wallet_initialized wallet_initialized))
(assert
 (= init_callable init_callable))
(assert
 (= attacker_is_admin_after attacker_is_admin_after))
(define-fun report_preconditions () Bool (and wallet_initialized init_callable wallet_initialized))
(define-fun report_safety () Bool (=> (and wallet_initialized init_callable) (not attacker_is_admin_after)))
(define-fun report_effects () Bool (and wallet_initialized init_callable (not (not attacker_is_admin_after))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
