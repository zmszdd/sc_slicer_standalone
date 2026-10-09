; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cumulative_price_read_occurred () Bool)
(declare-fun caller_supplied_tolerance_provided () Bool)
(declare-fun deviation_exceeds_tolerance () Bool)
(declare-fun twap_validation_result () Bool)
(assert
 (= cumulative_price_read_occurred cumulative_price_read_occurred))
(assert
 (= caller_supplied_tolerance_provided caller_supplied_tolerance_provided))
(assert
 (= deviation_exceeds_tolerance deviation_exceeds_tolerance))
(assert
 (= twap_validation_result twap_validation_result))
(define-fun report_preconditions () Bool (and cumulative_price_read_occurred caller_supplied_tolerance_provided))
(define-fun report_safety () Bool (=> (and cumulative_price_read_occurred
         caller_supplied_tolerance_provided
         deviation_exceeds_tolerance)
    (not twap_validation_result)))
(define-fun report_effects () Bool (and cumulative_price_read_occurred
     caller_supplied_tolerance_provided
     deviation_exceeds_tolerance
     (not (not twap_validation_result))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
