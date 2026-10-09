; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun validate_price_deviation_call () Bool)
(declare-fun guard_returns_true () Bool)
(assert
 (= validate_price_deviation_call validate_price_deviation_call))
(assert
 (= guard_returns_true guard_returns_true))
(define-fun report_preconditions () Bool (and validate_price_deviation_call validate_price_deviation_call))
(define-fun report_safety () Bool (=> validate_price_deviation_call (not guard_returns_true)))
(define-fun report_effects () Bool (and validate_price_deviation_call (not (not guard_returns_true))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
