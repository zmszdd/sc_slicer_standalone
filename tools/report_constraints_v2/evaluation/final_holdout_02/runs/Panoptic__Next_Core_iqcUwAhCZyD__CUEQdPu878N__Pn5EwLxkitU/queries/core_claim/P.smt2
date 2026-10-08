; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun init_publicly_callable () Bool)
(declare-fun caller_is_any_eoa () Bool)
(declare-fun builder_admin_overwritten () Bool)
(assert
 (= init_publicly_callable init_publicly_callable))
(assert
 (= caller_is_any_eoa caller_is_any_eoa))
(assert
 (= builder_admin_overwritten builder_admin_overwritten))
(define-fun report_preconditions () Bool (and init_publicly_callable caller_is_any_eoa))
(define-fun report_safety () Bool (=> (and init_publicly_callable caller_is_any_eoa)
    (not builder_admin_overwritten)))
(define-fun report_effects () Bool (and init_publicly_callable
     caller_is_any_eoa
     (not (not builder_admin_overwritten))))
(assert report_preconditions)
(check-sat)
(get-model)
