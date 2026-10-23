; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c112c77ee_init_callable_by_any_caller () Bool)
(declare-fun c112c77ee_init_reinitializable () Bool)
(declare-fun c112c77ee_sweep_authorized_by_legitimate_admin () Bool)
(declare-fun c112c77ee_sweep_gated_solely_by_builder_admin () Bool)
(declare-fun c112c77ee_wallet_drained () Bool)
(declare-fun c112c77ee_wallet_holds_erc20_balance () Bool)
(assert
 (= c112c77ee_init_callable_by_any_caller c112c77ee_init_callable_by_any_caller))
(assert
 (= c112c77ee_init_reinitializable c112c77ee_init_reinitializable))
(assert
 (= c112c77ee_sweep_authorized_by_legitimate_admin c112c77ee_sweep_authorized_by_legitimate_admin))
(assert
 (= c112c77ee_sweep_gated_solely_by_builder_admin c112c77ee_sweep_gated_solely_by_builder_admin))
(assert
 (= c112c77ee_wallet_drained c112c77ee_wallet_drained))
(assert
 (= c112c77ee_wallet_holds_erc20_balance c112c77ee_wallet_holds_erc20_balance))
(define-fun report_preconditions () Bool (and c112c77ee_wallet_holds_erc20_balance
     c112c77ee_init_callable_by_any_caller
     c112c77ee_init_reinitializable
     c112c77ee_sweep_gated_solely_by_builder_admin))
(define-fun report_safety () Bool (=> (and c112c77ee_wallet_holds_erc20_balance
         c112c77ee_sweep_gated_solely_by_builder_admin)
    (or c112c77ee_sweep_authorized_by_legitimate_admin
        (not c112c77ee_wallet_drained))))
(define-fun report_effects () Bool (and c112c77ee_wallet_holds_erc20_balance
     c112c77ee_sweep_gated_solely_by_builder_admin
     (not (or c112c77ee_sweep_authorized_by_legitimate_admin
              (not c112c77ee_wallet_drained)))))
(assert report_preconditions)
(check-sat)
(get-model)
