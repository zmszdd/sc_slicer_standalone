; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun caller_is_any_address () Bool)
(declare-fun init_sets_builder_admin () Bool)
(declare-fun builder_admin_overwritten () Bool)
(assert
 (= caller_is_any_address caller_is_any_address))
(assert
 (= init_sets_builder_admin init_sets_builder_admin))
(assert
 (= builder_admin_overwritten builder_admin_overwritten))
(define-fun report_preconditions () Bool (and caller_is_any_address init_sets_builder_admin))
(define-fun report_safety () Bool (=> (and caller_is_any_address init_sets_builder_admin)
    (not builder_admin_overwritten)))
(define-fun report_effects () Bool (and caller_is_any_address
     init_sets_builder_admin
     (not (not builder_admin_overwritten))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
