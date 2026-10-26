; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c367b7cdd_pool_in_manipulated_spot_regime () Bool)
(declare-fun c367b7cdd_price_far_from_original_reference () Bool)
(declare-fun c367b7cdd_validate_price_returns_true () Bool)
(assert
 (= c367b7cdd_pool_in_manipulated_spot_regime c367b7cdd_pool_in_manipulated_spot_regime))
(assert
 (= c367b7cdd_price_far_from_original_reference c367b7cdd_price_far_from_original_reference))
(assert
 (= c367b7cdd_validate_price_returns_true c367b7cdd_validate_price_returns_true))
(define-fun report_preconditions () Bool c367b7cdd_pool_in_manipulated_spot_regime)
(define-fun report_safety () Bool (=> c367b7cdd_price_far_from_original_reference
    (not c367b7cdd_validate_price_returns_true)))
(define-fun report_effects () Bool (and c367b7cdd_validate_price_returns_true
     c367b7cdd_price_far_from_original_reference
     c367b7cdd_pool_in_manipulated_spot_regime))
(assert report_preconditions)
(check-sat)
(get-model)
