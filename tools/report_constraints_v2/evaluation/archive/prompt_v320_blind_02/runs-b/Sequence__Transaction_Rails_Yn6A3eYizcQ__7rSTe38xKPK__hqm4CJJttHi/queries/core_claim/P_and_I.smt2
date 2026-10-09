; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun router_balance_nonzero () Bool)
(declare-fun inject_and_call_public_no_guard () Bool)
(declare-fun attacker_target_available () Bool)
(declare-fun direct_call_spends_router_funds () Bool)
(assert
 (= router_balance_nonzero router_balance_nonzero))
(assert
 (= inject_and_call_public_no_guard inject_and_call_public_no_guard))
(assert
 (= attacker_target_available attacker_target_available))
(assert
 (= direct_call_spends_router_funds direct_call_spends_router_funds))
(define-fun report_preconditions () Bool (and router_balance_nonzero
     inject_and_call_public_no_guard
     attacker_target_available))
(define-fun report_safety () Bool (=> (and router_balance_nonzero
         inject_and_call_public_no_guard
         attacker_target_available)
    (not direct_call_spends_router_funds)))
(define-fun report_effects () Bool (and router_balance_nonzero
     inject_and_call_public_no_guard
     attacker_target_available
     (not (not direct_call_spends_router_funds))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
