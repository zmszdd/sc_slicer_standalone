; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cea5427e0_buyback_callable_by_anyone () Bool)
(declare-fun cea5427e0_current_spot_price () Int)
(declare-fun cea5427e0_effective_pre_swap_price_validation () Bool)
(declare-fun cea5427e0_twap_reference_price () Int)
(declare-fun cea5427e0_validate_price_invoked () Bool)
(assert
 (= cea5427e0_buyback_callable_by_anyone cea5427e0_buyback_callable_by_anyone))
(assert
 (= cea5427e0_current_spot_price cea5427e0_current_spot_price))
(assert
 (= cea5427e0_effective_pre_swap_price_validation cea5427e0_effective_pre_swap_price_validation))
(assert
 (= cea5427e0_twap_reference_price cea5427e0_twap_reference_price))
(assert
 (= cea5427e0_validate_price_invoked cea5427e0_validate_price_invoked))
(define-fun report_preconditions () Bool (and cea5427e0_buyback_callable_by_anyone cea5427e0_validate_price_invoked))
(define-fun report_safety () Bool (= cea5427e0_current_spot_price cea5427e0_twap_reference_price))
(define-fun report_effects () Bool (and cea5427e0_validate_price_invoked
     (not (= cea5427e0_current_spot_price cea5427e0_twap_reference_price))
     (not cea5427e0_effective_pre_swap_price_validation)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
