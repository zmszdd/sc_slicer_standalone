; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun validate_price_called () Bool)
(declare-fun spot_price_manipulated () Bool)
(declare-fun slippage_tolerance_configured () Bool)
(declare-fun manipulated_price_accepted () Bool)
(assert
 (= validate_price_called validate_price_called))
(assert
 (= spot_price_manipulated spot_price_manipulated))
(assert
 (= slippage_tolerance_configured slippage_tolerance_configured))
(assert
 (= manipulated_price_accepted manipulated_price_accepted))
(define-fun report_preconditions () Bool (and validate_price_called spot_price_manipulated slippage_tolerance_configured))
(define-fun report_safety () Bool (=> (and validate_price_called
         spot_price_manipulated
         slippage_tolerance_configured)
    (not manipulated_price_accepted)))
(define-fun report_effects () Bool (and validate_price_called
     spot_price_manipulated
     slippage_tolerance_configured
     (not (not manipulated_price_accepted))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
