; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1be672c8_factory_vault_is_lpvault1 () Bool)
(declare-fun c1be672c8_fee_calc_returns_zero () Bool)
(declare-fun c1be672c8_pair_uses_lpvault1 () Bool)
(assert
 (= c1be672c8_factory_vault_is_lpvault1 c1be672c8_factory_vault_is_lpvault1))
(assert
 (= c1be672c8_fee_calc_returns_zero c1be672c8_fee_calc_returns_zero))
(assert
 (= c1be672c8_pair_uses_lpvault1 c1be672c8_pair_uses_lpvault1))
(define-fun report_preconditions () Bool (and c1be672c8_factory_vault_is_lpvault1 c1be672c8_pair_uses_lpvault1))
(define-fun report_safety () Bool (=> (and c1be672c8_factory_vault_is_lpvault1 c1be672c8_pair_uses_lpvault1)
    (not c1be672c8_fee_calc_returns_zero)))
(define-fun report_effects () Bool (and c1be672c8_factory_vault_is_lpvault1
     c1be672c8_pair_uses_lpvault1
     (not (not c1be672c8_fee_calc_returns_zero))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
