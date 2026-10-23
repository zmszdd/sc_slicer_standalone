; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7db53e3c_erc20_theft_occurred () Bool)
(declare-fun c7db53e3c_init_callable_by_any_caller () Bool)
(declare-fun c7db53e3c_init_reinitializable () Bool)
(declare-fun c7db53e3c_sweep_authorized_by_legitimate_admin () Bool)
(declare-fun c7db53e3c_sweep_gated_solely_by_builder_admin () Bool)
(declare-fun c7db53e3c_wallet_holds_erc20_balance () Bool)
(assert
 (= c7db53e3c_erc20_theft_occurred c7db53e3c_erc20_theft_occurred))
(assert
 (= c7db53e3c_init_callable_by_any_caller c7db53e3c_init_callable_by_any_caller))
(assert
 (= c7db53e3c_init_reinitializable c7db53e3c_init_reinitializable))
(assert
 (= c7db53e3c_sweep_authorized_by_legitimate_admin c7db53e3c_sweep_authorized_by_legitimate_admin))
(assert
 (= c7db53e3c_sweep_gated_solely_by_builder_admin c7db53e3c_sweep_gated_solely_by_builder_admin))
(assert
 (= c7db53e3c_wallet_holds_erc20_balance c7db53e3c_wallet_holds_erc20_balance))
(define-fun report_preconditions () Bool (and c7db53e3c_wallet_holds_erc20_balance
     c7db53e3c_init_callable_by_any_caller
     c7db53e3c_init_reinitializable
     c7db53e3c_sweep_gated_solely_by_builder_admin))
(define-fun report_safety () Bool (=> (and c7db53e3c_wallet_holds_erc20_balance
         c7db53e3c_sweep_gated_solely_by_builder_admin)
    (or c7db53e3c_sweep_authorized_by_legitimate_admin
        (not c7db53e3c_erc20_theft_occurred))))
(define-fun report_effects () Bool (and c7db53e3c_wallet_holds_erc20_balance
     c7db53e3c_sweep_gated_solely_by_builder_admin
     (not (or c7db53e3c_sweep_authorized_by_legitimate_admin
              (not c7db53e3c_erc20_theft_occurred)))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
