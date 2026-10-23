; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1ff8b0eb_builder_admin_overwritten () Bool)
(declare-fun c1ff8b0eb_caller_is_arbitrary_user () Bool)
(declare-fun c1ff8b0eb_init_has_access_control () Bool)
(declare-fun c1ff8b0eb_sweep_caller_is_legitimate_admin () Bool)
(declare-fun c1ff8b0eb_wallet_tokens_drained () Bool)
(assert
 (= c1ff8b0eb_builder_admin_overwritten c1ff8b0eb_builder_admin_overwritten))
(assert
 (= c1ff8b0eb_caller_is_arbitrary_user c1ff8b0eb_caller_is_arbitrary_user))
(assert
 (= c1ff8b0eb_init_has_access_control c1ff8b0eb_init_has_access_control))
(assert
 (= c1ff8b0eb_sweep_caller_is_legitimate_admin c1ff8b0eb_sweep_caller_is_legitimate_admin))
(assert
 (= c1ff8b0eb_wallet_tokens_drained c1ff8b0eb_wallet_tokens_drained))
(define-fun report_preconditions () Bool (and (not c1ff8b0eb_init_has_access_control)
     c1ff8b0eb_caller_is_arbitrary_user
     c1ff8b0eb_builder_admin_overwritten))
(define-fun report_safety () Bool (=> (and (not c1ff8b0eb_init_has_access_control)
         c1ff8b0eb_caller_is_arbitrary_user
         c1ff8b0eb_builder_admin_overwritten)
    (or c1ff8b0eb_sweep_caller_is_legitimate_admin
        (not c1ff8b0eb_wallet_tokens_drained))))
(define-fun report_effects () Bool (and (not c1ff8b0eb_init_has_access_control)
     c1ff8b0eb_caller_is_arbitrary_user
     c1ff8b0eb_builder_admin_overwritten
     (not (or c1ff8b0eb_sweep_caller_is_legitimate_admin
              (not c1ff8b0eb_wallet_tokens_drained)))))
