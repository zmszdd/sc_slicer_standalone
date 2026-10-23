; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1fbf9de3_inject_and_call_available () Bool)
(declare-fun c1fbf9de3_router_funds_drained () Bool)
(assert
 (= c1fbf9de3_inject_and_call_available c1fbf9de3_inject_and_call_available))
(assert
 (= c1fbf9de3_router_funds_drained c1fbf9de3_router_funds_drained))
(define-fun report_preconditions () Bool c1fbf9de3_inject_and_call_available)
(define-fun report_safety () Bool (=> c1fbf9de3_inject_and_call_available (not c1fbf9de3_router_funds_drained)))
(define-fun report_effects () Bool (and c1fbf9de3_inject_and_call_available
     (not (not c1fbf9de3_router_funds_drained))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
