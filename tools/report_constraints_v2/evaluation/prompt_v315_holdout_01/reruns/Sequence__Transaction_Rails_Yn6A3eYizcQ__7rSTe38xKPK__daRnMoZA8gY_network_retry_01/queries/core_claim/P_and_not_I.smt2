; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun inject_and_call_public () Bool)
(declare-fun anyone_can_call () Bool)
(declare-fun attacker_targets () Bool)
(declare-fun router_holds_balances () Bool)
(declare-fun erc20_drained () Bool)
(declare-fun delegatecall_context_authorized () Bool)
(declare-fun token_transfer_authorized () Bool)
(declare-fun external_call_move_authorized () Bool)
(assert
 (= inject_and_call_public inject_and_call_public))
(assert
 (= anyone_can_call anyone_can_call))
(assert
 (= attacker_targets attacker_targets))
(assert
 (= router_holds_balances router_holds_balances))
(assert
 (= erc20_drained erc20_drained))
(assert
 (= delegatecall_context_authorized delegatecall_context_authorized))
(assert
 (= token_transfer_authorized token_transfer_authorized))
(assert
 (= external_call_move_authorized external_call_move_authorized))
(define-fun report_preconditions () Bool (and inject_and_call_public
     anyone_can_call
     attacker_targets
     router_holds_balances))
(define-fun report_safety () Bool (=> erc20_drained
    (or delegatecall_context_authorized
        token_transfer_authorized
        external_call_move_authorized)))
(define-fun report_effects () Bool (and erc20_drained
     (not (or delegatecall_context_authorized
              token_transfer_authorized
              external_call_move_authorized))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
