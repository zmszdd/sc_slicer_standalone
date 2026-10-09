; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun router_funds_present () Bool)
(declare-fun injectandcall_public () Bool)
(declare-fun target_caller_chosen () Bool)
(declare-fun router_approves_target_balance () Bool)
(assert
 (= router_funds_present router_funds_present))
(assert
 (= injectandcall_public injectandcall_public))
(assert
 (= target_caller_chosen target_caller_chosen))
(assert
 (= router_approves_target_balance router_approves_target_balance))
(define-fun report_preconditions () Bool (and router_funds_present injectandcall_public target_caller_chosen))
(define-fun report_safety () Bool (=> router_funds_present (not router_approves_target_balance)))
(define-fun report_effects () Bool (and router_funds_present router_approves_target_balance))
(assert report_preconditions)
(check-sat)
(get-model)
