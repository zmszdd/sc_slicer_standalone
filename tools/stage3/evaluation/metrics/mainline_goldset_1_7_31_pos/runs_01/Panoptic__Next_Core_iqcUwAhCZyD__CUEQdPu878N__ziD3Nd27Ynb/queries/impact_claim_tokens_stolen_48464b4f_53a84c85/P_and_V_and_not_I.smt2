; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7343112a_all_accumulated_tokens_stolen () Bool)
(declare-fun c7343112a_builder_admin_hijacked_by_unauthorized () Bool)
(declare-fun c7343112a_owner_call_mempool_visible () Bool)
(declare-fun c7343112a_owner_initiated_deployment () Bool)
(declare-fun c7343112a_sweep_control_with_legitimate_admin () Bool)
(declare-fun c7343112a_wallet_address_predictable () Bool)
(assert
 (= c7343112a_all_accumulated_tokens_stolen c7343112a_all_accumulated_tokens_stolen))
(assert
 (= c7343112a_builder_admin_hijacked_by_unauthorized c7343112a_builder_admin_hijacked_by_unauthorized))
(assert
 (= c7343112a_owner_call_mempool_visible c7343112a_owner_call_mempool_visible))
(assert
 (= c7343112a_owner_initiated_deployment c7343112a_owner_initiated_deployment))
(assert
 (= c7343112a_sweep_control_with_legitimate_admin c7343112a_sweep_control_with_legitimate_admin))
(assert
 (= c7343112a_wallet_address_predictable c7343112a_wallet_address_predictable))
(define-fun report_preconditions () Bool (and c7343112a_owner_initiated_deployment
     c7343112a_owner_call_mempool_visible
     c7343112a_wallet_address_predictable))
(define-fun report_safety () Bool (=> c7343112a_sweep_control_with_legitimate_admin
    (not c7343112a_builder_admin_hijacked_by_unauthorized)))
(define-fun report_effects () Bool (and c7343112a_sweep_control_with_legitimate_admin
     c7343112a_builder_admin_hijacked_by_unauthorized
     c7343112a_all_accumulated_tokens_stolen
     c7343112a_all_accumulated_tokens_stolen))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
