; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4d5de2ca_delegatecall_context_used () Bool)
(declare-fun c4d5de2ca_funds_remain_no_recovery () Bool)
(declare-fun c4d5de2ca_router_balance_after_direct_call () Int)
(declare-fun c4d5de2ca_zero_balance () Int)
(assert
 (= c4d5de2ca_delegatecall_context_used c4d5de2ca_delegatecall_context_used))
(assert
 (= c4d5de2ca_funds_remain_no_recovery c4d5de2ca_funds_remain_no_recovery))
(assert
 (= c4d5de2ca_router_balance_after_direct_call c4d5de2ca_router_balance_after_direct_call))
(assert
 (= c4d5de2ca_zero_balance c4d5de2ca_zero_balance))
(define-fun report_preconditions () Bool c4d5de2ca_delegatecall_context_used)
(define-fun report_safety () Bool (=> c4d5de2ca_delegatecall_context_used
    (<= c4d5de2ca_router_balance_after_direct_call c4d5de2ca_zero_balance)))
(define-fun report_effects () Bool (and c4d5de2ca_delegatecall_context_used
     (not (<= c4d5de2ca_router_balance_after_direct_call c4d5de2ca_zero_balance))
     (> c4d5de2ca_router_balance_after_direct_call c4d5de2ca_zero_balance)
     c4d5de2ca_funds_remain_no_recovery
     c4d5de2ca_funds_remain_no_recovery))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
