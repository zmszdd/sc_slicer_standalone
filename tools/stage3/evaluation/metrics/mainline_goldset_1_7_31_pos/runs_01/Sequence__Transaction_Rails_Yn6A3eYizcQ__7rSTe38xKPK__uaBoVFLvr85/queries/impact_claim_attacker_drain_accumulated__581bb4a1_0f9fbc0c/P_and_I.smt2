; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c95aa5e49_accumulated_balances_drained () Bool)
(declare-fun c95aa5e49_delegatecall_only_guard_present () Bool)
(declare-fun c95aa5e49_inject_sweep_and_call_executes () Bool)
(declare-fun c95aa5e49_router_executes_via_delegatecall () Bool)
(assert
 (= c95aa5e49_accumulated_balances_drained c95aa5e49_accumulated_balances_drained))
(assert
 (= c95aa5e49_delegatecall_only_guard_present c95aa5e49_delegatecall_only_guard_present))
(assert
 (= c95aa5e49_inject_sweep_and_call_executes c95aa5e49_inject_sweep_and_call_executes))
(assert
 (= c95aa5e49_router_executes_via_delegatecall c95aa5e49_router_executes_via_delegatecall))
(define-fun report_preconditions () Bool c95aa5e49_router_executes_via_delegatecall)
(define-fun report_safety () Bool (=> c95aa5e49_inject_sweep_and_call_executes
    c95aa5e49_delegatecall_only_guard_present))
(define-fun report_effects () Bool (and c95aa5e49_inject_sweep_and_call_executes
     (not c95aa5e49_delegatecall_only_guard_present)
     c95aa5e49_accumulated_balances_drained))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
