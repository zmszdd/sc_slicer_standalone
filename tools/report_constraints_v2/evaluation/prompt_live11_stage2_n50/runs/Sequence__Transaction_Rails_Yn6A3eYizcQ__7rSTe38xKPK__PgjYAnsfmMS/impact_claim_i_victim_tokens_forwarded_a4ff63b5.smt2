; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c033463dd_caller_entitled_to_assets () Bool)
(declare-fun c033463dd_router_holds_balance () Bool)
(declare-fun c033463dd_target_is_caller_chosen () Bool)
(declare-fun c033463dd_victim_tokens_forwarded_out () Bool)
(assert
 (= c033463dd_caller_entitled_to_assets c033463dd_caller_entitled_to_assets))
(assert
 (= c033463dd_router_holds_balance c033463dd_router_holds_balance))
(assert
 (= c033463dd_target_is_caller_chosen c033463dd_target_is_caller_chosen))
(assert
 (= c033463dd_victim_tokens_forwarded_out c033463dd_victim_tokens_forwarded_out))
(define-fun report_preconditions () Bool (and c033463dd_router_holds_balance c033463dd_target_is_caller_chosen))
(define-fun report_safety () Bool (=> (and c033463dd_router_holds_balance c033463dd_target_is_caller_chosen)
    (or c033463dd_caller_entitled_to_assets
        (not c033463dd_victim_tokens_forwarded_out))))
(define-fun report_effects () Bool (and c033463dd_router_holds_balance
     c033463dd_target_is_caller_chosen
     (not (or c033463dd_caller_entitled_to_assets
              (not c033463dd_victim_tokens_forwarded_out)))))
