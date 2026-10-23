; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c727994a3_executed_in_delegatecall_context () Bool)
(declare-fun c727994a3_funds_remain_in_router () Bool)
(declare-fun c727994a3_inject_sweep_and_call_is_external () Bool)
(declare-fun c727994a3_users_send_funds_to_router () Bool)
(assert
 (= c727994a3_executed_in_delegatecall_context c727994a3_executed_in_delegatecall_context))
(assert
 (= c727994a3_funds_remain_in_router c727994a3_funds_remain_in_router))
(assert
 (= c727994a3_inject_sweep_and_call_is_external c727994a3_inject_sweep_and_call_is_external))
(assert
 (= c727994a3_users_send_funds_to_router c727994a3_users_send_funds_to_router))
(define-fun report_preconditions () Bool (and c727994a3_inject_sweep_and_call_is_external
     c727994a3_users_send_funds_to_router))
(define-fun report_safety () Bool (=> (and c727994a3_inject_sweep_and_call_is_external
         c727994a3_users_send_funds_to_router)
    (or c727994a3_executed_in_delegatecall_context
        (not c727994a3_funds_remain_in_router))))
(define-fun report_effects () Bool (and c727994a3_inject_sweep_and_call_is_external
     c727994a3_users_send_funds_to_router
     (not (or c727994a3_executed_in_delegatecall_context
              (not c727994a3_funds_remain_in_router)))))
