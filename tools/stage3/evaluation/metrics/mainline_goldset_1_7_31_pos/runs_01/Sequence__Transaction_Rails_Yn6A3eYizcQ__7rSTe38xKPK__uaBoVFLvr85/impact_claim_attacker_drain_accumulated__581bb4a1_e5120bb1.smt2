; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8695e9c2_attacker_drains_router_balances () Bool)
(declare-fun c8695e9c2_router_holds_no_long_term_funds () Bool)
(declare-fun c8695e9c2_router_holds_user_funds () Bool)
(declare-fun c8695e9c2_router_used_via_delegatecall () Bool)
(assert
 (= c8695e9c2_attacker_drains_router_balances c8695e9c2_attacker_drains_router_balances))
(assert
 (= c8695e9c2_router_holds_no_long_term_funds c8695e9c2_router_holds_no_long_term_funds))
(assert
 (= c8695e9c2_router_holds_user_funds c8695e9c2_router_holds_user_funds))
(assert
 (= c8695e9c2_router_used_via_delegatecall c8695e9c2_router_used_via_delegatecall))
(define-fun report_preconditions () Bool (and c8695e9c2_router_used_via_delegatecall c8695e9c2_router_holds_user_funds))
(define-fun report_safety () Bool (= c8695e9c2_router_holds_user_funds c8695e9c2_router_holds_no_long_term_funds))
(define-fun report_effects () Bool (and c8695e9c2_router_holds_user_funds
     (not (= c8695e9c2_router_holds_user_funds
             c8695e9c2_router_holds_no_long_term_funds))
     c8695e9c2_attacker_drains_router_balances))
