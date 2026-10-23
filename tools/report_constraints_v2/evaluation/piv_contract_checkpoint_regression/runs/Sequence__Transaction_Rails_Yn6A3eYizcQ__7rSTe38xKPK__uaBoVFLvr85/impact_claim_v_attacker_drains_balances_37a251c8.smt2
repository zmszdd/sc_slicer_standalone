; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c97908255_called_directly_on_router () Bool)
(declare-fun c97908255_function_lacks_delegatecall_guard () Bool)
(declare-fun c97908255_router_balance_drained_by_attacker () Bool)
(declare-fun c97908255_target_misconfigured_or_fails () Bool)
(declare-fun c97908255_user_funds_sent_to_router () Bool)
(assert
 (= c97908255_called_directly_on_router c97908255_called_directly_on_router))
(assert
 (= c97908255_function_lacks_delegatecall_guard c97908255_function_lacks_delegatecall_guard))
(assert
 (= c97908255_router_balance_drained_by_attacker c97908255_router_balance_drained_by_attacker))
(assert
 (= c97908255_target_misconfigured_or_fails c97908255_target_misconfigured_or_fails))
(assert
 (= c97908255_user_funds_sent_to_router c97908255_user_funds_sent_to_router))
(define-fun report_preconditions () Bool (and c97908255_function_lacks_delegatecall_guard
     c97908255_called_directly_on_router
     c97908255_user_funds_sent_to_router
     c97908255_target_misconfigured_or_fails))
(define-fun report_safety () Bool (=> (and c97908255_function_lacks_delegatecall_guard
         c97908255_called_directly_on_router
         c97908255_user_funds_sent_to_router)
    (not c97908255_router_balance_drained_by_attacker)))
(define-fun report_effects () Bool (and c97908255_function_lacks_delegatecall_guard
     c97908255_called_directly_on_router
     c97908255_user_funds_sent_to_router
     (not (not c97908255_router_balance_drained_by_attacker))))
