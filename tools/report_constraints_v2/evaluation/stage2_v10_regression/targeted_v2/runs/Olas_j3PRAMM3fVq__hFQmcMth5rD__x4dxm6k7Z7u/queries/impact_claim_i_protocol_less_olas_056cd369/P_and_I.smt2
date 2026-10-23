; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cfa8223b1_amount_out_minimum () Int)
(declare-fun cfa8223b1_effective_slippage_protection_enforced () Bool)
(declare-fun cfa8223b1_pending_buyback_observable () Bool)
(declare-fun cfa8223b1_post_swap_validation_present () Bool)
(declare-fun cfa8223b1_protocol_receives_less_than_fair_olas () Bool)
(declare-fun cfa8223b1_sqrt_price_limit_x96 () Int)
(assert
 (= cfa8223b1_amount_out_minimum cfa8223b1_amount_out_minimum))
(assert
 (= cfa8223b1_effective_slippage_protection_enforced cfa8223b1_effective_slippage_protection_enforced))
(assert
 (= cfa8223b1_pending_buyback_observable cfa8223b1_pending_buyback_observable))
(assert
 (= cfa8223b1_post_swap_validation_present cfa8223b1_post_swap_validation_present))
(assert
 (= cfa8223b1_protocol_receives_less_than_fair_olas cfa8223b1_protocol_receives_less_than_fair_olas))
(assert
 (= cfa8223b1_sqrt_price_limit_x96 cfa8223b1_sqrt_price_limit_x96))
(define-fun report_preconditions () Bool (and cfa8223b1_pending_buyback_observable
     (= 1 cfa8223b1_amount_out_minimum)
     (= 0 cfa8223b1_sqrt_price_limit_x96)
     (not cfa8223b1_post_swap_validation_present)))
(define-fun report_safety () Bool (=> (and cfa8223b1_pending_buyback_observable
         (= 1 cfa8223b1_amount_out_minimum)
         (= 0 cfa8223b1_sqrt_price_limit_x96)
         (not cfa8223b1_post_swap_validation_present))
    (and cfa8223b1_effective_slippage_protection_enforced
         (not cfa8223b1_protocol_receives_less_than_fair_olas))))
(define-fun report_effects () Bool (and cfa8223b1_pending_buyback_observable
     (= 1 cfa8223b1_amount_out_minimum)
     (= 0 cfa8223b1_sqrt_price_limit_x96)
     (not cfa8223b1_post_swap_validation_present)
     (not (and cfa8223b1_effective_slippage_protection_enforced
               (not cfa8223b1_protocol_receives_less_than_fair_olas)))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
