; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1746d2bb_router_accumulates_user_funds () Bool)
(declare-fun c1746d2bb_router_executes_in_delegatecall_context () Bool)
(declare-fun c1746d2bb_router_holds_no_long_term_funds () Bool)
(declare-fun c1746d2bb_router_used_via_delegatecall () Bool)
(declare-fun c1746d2bb_self_balance_owner_is_wallet () Bool)
(declare-fun c1746d2bb_user_sends_funds_to_router () Bool)
(assert
 (= c1746d2bb_router_accumulates_user_funds c1746d2bb_router_accumulates_user_funds))
(assert
 (= c1746d2bb_router_executes_in_delegatecall_context c1746d2bb_router_executes_in_delegatecall_context))
(assert
 (= c1746d2bb_router_holds_no_long_term_funds c1746d2bb_router_holds_no_long_term_funds))
(assert
 (= c1746d2bb_router_used_via_delegatecall c1746d2bb_router_used_via_delegatecall))
(assert
 (= c1746d2bb_self_balance_owner_is_wallet c1746d2bb_self_balance_owner_is_wallet))
(assert
 (= c1746d2bb_user_sends_funds_to_router c1746d2bb_user_sends_funds_to_router))
(define-fun report_preconditions () Bool (and c1746d2bb_router_used_via_delegatecall
     c1746d2bb_self_balance_owner_is_wallet))
(define-fun report_safety () Bool (=> c1746d2bb_router_executes_in_delegatecall_context
    (= c1746d2bb_router_accumulates_user_funds
       c1746d2bb_router_holds_no_long_term_funds)))
(define-fun report_effects () Bool (and c1746d2bb_router_executes_in_delegatecall_context
     (not (= c1746d2bb_router_accumulates_user_funds
             c1746d2bb_router_holds_no_long_term_funds))
     c1746d2bb_user_sends_funds_to_router
     c1746d2bb_router_accumulates_user_funds))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
