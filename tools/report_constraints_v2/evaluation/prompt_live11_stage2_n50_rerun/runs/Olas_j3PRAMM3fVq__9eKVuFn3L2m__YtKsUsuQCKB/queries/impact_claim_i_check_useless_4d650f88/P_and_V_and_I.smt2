; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c92580c64_twap_equals_spot () Bool)
(declare-fun c92580c64_validate_price_invoked () Bool)
(assert
 (= c92580c64_twap_equals_spot c92580c64_twap_equals_spot))
(assert
 (= c92580c64_validate_price_invoked c92580c64_validate_price_invoked))
(define-fun report_preconditions () Bool c92580c64_validate_price_invoked)
(define-fun report_safety () Bool (=> c92580c64_validate_price_invoked (not c92580c64_twap_equals_spot)))
(define-fun report_effects () Bool (and c92580c64_validate_price_invoked (not (not c92580c64_twap_equals_spot))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
