; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce63a0fc0_execution_context_is_delegatecall () Bool)
(declare-fun ce63a0fc0_router_holds_user_funds () Bool)
(assert
 (= ce63a0fc0_execution_context_is_delegatecall ce63a0fc0_execution_context_is_delegatecall))
(assert
 (= ce63a0fc0_router_holds_user_funds ce63a0fc0_router_holds_user_funds))
(define-fun report_preconditions () Bool ce63a0fc0_execution_context_is_delegatecall)
(define-fun report_safety () Bool (=> ce63a0fc0_execution_context_is_delegatecall
    (not ce63a0fc0_router_holds_user_funds)))
(define-fun report_effects () Bool (and ce63a0fc0_execution_context_is_delegatecall
     (not (not ce63a0fc0_router_holds_user_funds))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
