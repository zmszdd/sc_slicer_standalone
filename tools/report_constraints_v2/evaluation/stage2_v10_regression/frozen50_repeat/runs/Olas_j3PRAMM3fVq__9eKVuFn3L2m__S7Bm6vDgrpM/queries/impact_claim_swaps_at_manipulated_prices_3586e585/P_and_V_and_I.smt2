; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6748476f_spot_price_manipulated () Bool)
(declare-fun c6748476f_swap_executed_at_manipulated_price () Bool)
(declare-fun c6748476f_twap_derived_from_history () Bool)
(assert
 (= c6748476f_spot_price_manipulated c6748476f_spot_price_manipulated))
(assert
 (= c6748476f_swap_executed_at_manipulated_price c6748476f_swap_executed_at_manipulated_price))
(assert
 (= c6748476f_twap_derived_from_history c6748476f_twap_derived_from_history))
(define-fun report_preconditions () Bool c6748476f_spot_price_manipulated)
(define-fun report_safety () Bool (=> c6748476f_spot_price_manipulated
    (or c6748476f_twap_derived_from_history
        (not c6748476f_swap_executed_at_manipulated_price))))
(define-fun report_effects () Bool (and c6748476f_spot_price_manipulated
     (not (or c6748476f_twap_derived_from_history
              (not c6748476f_swap_executed_at_manipulated_price)))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
