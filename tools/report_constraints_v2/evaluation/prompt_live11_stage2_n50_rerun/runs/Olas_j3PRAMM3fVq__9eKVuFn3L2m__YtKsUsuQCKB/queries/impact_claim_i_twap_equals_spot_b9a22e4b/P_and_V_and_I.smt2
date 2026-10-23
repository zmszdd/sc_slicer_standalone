; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2da34e4b_spot_price () Int)
(declare-fun c2da34e4b_twap_value () Int)
(declare-fun c2da34e4b_validate_price_invoked () Bool)
(assert
 (= c2da34e4b_spot_price c2da34e4b_spot_price))
(assert
 (= c2da34e4b_twap_value c2da34e4b_twap_value))
(assert
 (= c2da34e4b_validate_price_invoked c2da34e4b_validate_price_invoked))
(define-fun report_preconditions () Bool c2da34e4b_validate_price_invoked)
(define-fun report_safety () Bool (=> c2da34e4b_validate_price_invoked
    (distinct c2da34e4b_twap_value c2da34e4b_spot_price)))
(define-fun report_effects () Bool (and c2da34e4b_validate_price_invoked
     (not (distinct c2da34e4b_twap_value c2da34e4b_spot_price))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
