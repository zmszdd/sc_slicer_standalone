; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun init_caller_authorized () Bool)
(declare-fun admin_overwritten () Bool)
(declare-fun admin_guard_active () Bool)
(assert
 (= init_caller_authorized init_caller_authorized))
(assert
 (= admin_overwritten admin_overwritten))
(assert
 (= admin_guard_active admin_guard_active))
(define-fun report_preconditions () Bool (and (not init_caller_authorized) admin_guard_active))
(define-fun report_safety () Bool (=> (not init_caller_authorized) (not admin_overwritten)))
(define-fun report_effects () Bool (and (not init_caller_authorized) admin_overwritten))
(assert report_preconditions)
(check-sat)
(get-model)
