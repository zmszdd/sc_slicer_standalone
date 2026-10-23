; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c909ecf7d_executes_in_delegatecall_context () Bool)
(declare-fun c909ecf7d_router_holds_user_funds () Bool)
(declare-fun c909ecf7d_target_misconfigured_or_fails () Bool)
(declare-fun c909ecf7d_users_send_funds_to_router () Bool)
(assert
 (= c909ecf7d_executes_in_delegatecall_context c909ecf7d_executes_in_delegatecall_context))
(assert
 (= c909ecf7d_router_holds_user_funds c909ecf7d_router_holds_user_funds))
(assert
 (= c909ecf7d_target_misconfigured_or_fails c909ecf7d_target_misconfigured_or_fails))
(assert
 (= c909ecf7d_users_send_funds_to_router c909ecf7d_users_send_funds_to_router))
(define-fun report_preconditions () Bool (and c909ecf7d_executes_in_delegatecall_context
     c909ecf7d_users_send_funds_to_router
     c909ecf7d_target_misconfigured_or_fails))
(define-fun report_safety () Bool (=> (and c909ecf7d_executes_in_delegatecall_context
         c909ecf7d_users_send_funds_to_router)
    (not c909ecf7d_router_holds_user_funds)))
(define-fun report_effects () Bool (and c909ecf7d_executes_in_delegatecall_context
     c909ecf7d_users_send_funds_to_router
     (not (not c909ecf7d_router_holds_user_funds))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
