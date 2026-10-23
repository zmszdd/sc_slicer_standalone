; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce54f4878_direct_call_context () Bool)
(declare-fun ce54f4878_inject_and_call_available () Bool)
(declare-fun ce54f4878_router_funds_used_as_injected_balance () Bool)
(assert
 (= ce54f4878_direct_call_context ce54f4878_direct_call_context))
(assert
 (= ce54f4878_inject_and_call_available ce54f4878_inject_and_call_available))
(assert
 (= ce54f4878_router_funds_used_as_injected_balance ce54f4878_router_funds_used_as_injected_balance))
(define-fun report_preconditions () Bool ce54f4878_inject_and_call_available)
(define-fun report_safety () Bool (=> (and ce54f4878_inject_and_call_available ce54f4878_direct_call_context)
    (not ce54f4878_router_funds_used_as_injected_balance)))
(define-fun report_effects () Bool (and ce54f4878_inject_and_call_available
     ce54f4878_direct_call_context
     (not (not ce54f4878_router_funds_used_as_injected_balance))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
