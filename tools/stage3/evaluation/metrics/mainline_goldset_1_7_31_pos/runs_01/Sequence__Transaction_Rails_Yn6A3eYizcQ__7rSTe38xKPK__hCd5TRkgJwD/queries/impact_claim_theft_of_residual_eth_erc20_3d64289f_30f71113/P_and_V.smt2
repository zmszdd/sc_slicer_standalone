; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6d81da3e_arbitrary_multicall3_target_moves_router_balance () Bool)
(declare-fun c6d81da3e_public_entrypoint_callable () Bool)
(declare-fun c6d81da3e_router_funds_exfiltrated () Bool)
(declare-fun c6d81da3e_router_holds_nonzero_funds () Bool)
(assert
 (= c6d81da3e_arbitrary_multicall3_target_moves_router_balance c6d81da3e_arbitrary_multicall3_target_moves_router_balance))
(assert
 (= c6d81da3e_public_entrypoint_callable c6d81da3e_public_entrypoint_callable))
(assert
 (= c6d81da3e_router_funds_exfiltrated c6d81da3e_router_funds_exfiltrated))
(assert
 (= c6d81da3e_router_holds_nonzero_funds c6d81da3e_router_holds_nonzero_funds))
(define-fun report_preconditions () Bool (and c6d81da3e_router_holds_nonzero_funds c6d81da3e_public_entrypoint_callable))
(define-fun report_safety () Bool (=> c6d81da3e_arbitrary_multicall3_target_moves_router_balance
    (not c6d81da3e_public_entrypoint_callable)))
(define-fun report_effects () Bool (and c6d81da3e_arbitrary_multicall3_target_moves_router_balance
     c6d81da3e_public_entrypoint_callable
     c6d81da3e_router_funds_exfiltrated
     c6d81da3e_arbitrary_multicall3_target_moves_router_balance))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
