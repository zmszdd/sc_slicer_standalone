; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3835d768_builder_admin_overwritten () Bool)
(declare-fun c3835d768_caller_is_arbitrary_user () Bool)
(declare-fun c3835d768_init_has_access_control () Bool)
(declare-fun c3835d768_wallet_holds_tokens () Bool)
(assert
 (= c3835d768_builder_admin_overwritten c3835d768_builder_admin_overwritten))
(assert
 (= c3835d768_caller_is_arbitrary_user c3835d768_caller_is_arbitrary_user))
(assert
 (= c3835d768_init_has_access_control c3835d768_init_has_access_control))
(assert
 (= c3835d768_wallet_holds_tokens c3835d768_wallet_holds_tokens))
(define-fun report_preconditions () Bool (and (not c3835d768_init_has_access_control)
     c3835d768_caller_is_arbitrary_user
     c3835d768_wallet_holds_tokens))
(define-fun report_safety () Bool (=> (and c3835d768_caller_is_arbitrary_user
         (not c3835d768_init_has_access_control))
    (not c3835d768_builder_admin_overwritten)))
(define-fun report_effects () Bool (and c3835d768_caller_is_arbitrary_user
     (not c3835d768_init_has_access_control)
     (not (not c3835d768_builder_admin_overwritten))))
