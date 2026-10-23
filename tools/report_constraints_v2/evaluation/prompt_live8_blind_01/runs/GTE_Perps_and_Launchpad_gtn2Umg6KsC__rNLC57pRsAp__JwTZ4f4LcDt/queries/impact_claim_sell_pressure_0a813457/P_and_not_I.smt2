; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3c34afa1_factory_vault_is_lpvault1 () Bool)
(declare-fun c3c34afa1_fee_vault_matches_current_vault () Bool)
(declare-fun c3c34afa1_pair_initialized_with_lpvault1 () Bool)
(declare-fun c3c34afa1_sell_pressure_arises () Bool)
(assert
 (= c3c34afa1_factory_vault_is_lpvault1 c3c34afa1_factory_vault_is_lpvault1))
(assert
 (= c3c34afa1_fee_vault_matches_current_vault c3c34afa1_fee_vault_matches_current_vault))
(assert
 (= c3c34afa1_pair_initialized_with_lpvault1 c3c34afa1_pair_initialized_with_lpvault1))
(assert
 (= c3c34afa1_sell_pressure_arises c3c34afa1_sell_pressure_arises))
(define-fun report_preconditions () Bool (and c3c34afa1_factory_vault_is_lpvault1
     c3c34afa1_pair_initialized_with_lpvault1))
(define-fun report_safety () Bool (=> (and c3c34afa1_factory_vault_is_lpvault1
         c3c34afa1_pair_initialized_with_lpvault1)
    (or c3c34afa1_fee_vault_matches_current_vault
        (not c3c34afa1_sell_pressure_arises))))
(define-fun report_effects () Bool (and c3c34afa1_factory_vault_is_lpvault1
     c3c34afa1_pair_initialized_with_lpvault1
     (not (or c3c34afa1_fee_vault_matches_current_vault
              (not c3c34afa1_sell_pressure_arises)))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
