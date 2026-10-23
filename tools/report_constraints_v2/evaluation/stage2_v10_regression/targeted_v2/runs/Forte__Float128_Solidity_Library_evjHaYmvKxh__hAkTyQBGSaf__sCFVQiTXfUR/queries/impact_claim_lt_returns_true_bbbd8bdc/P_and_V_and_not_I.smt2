; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0ea3a1f2_collateral_math_value () Int)
(declare-fun c0ea3a1f2_lt_result () Bool)
(declare-fun c0ea3a1f2_threshold_math_value () Int)
(assert
 (= c0ea3a1f2_collateral_math_value c0ea3a1f2_collateral_math_value))
(assert
 (= c0ea3a1f2_lt_result c0ea3a1f2_lt_result))
(assert
 (= c0ea3a1f2_threshold_math_value c0ea3a1f2_threshold_math_value))
(define-fun report_preconditions () Bool (and (= 10 c0ea3a1f2_threshold_math_value)
     (= 1000 c0ea3a1f2_collateral_math_value)
     (> c0ea3a1f2_collateral_math_value c0ea3a1f2_threshold_math_value)))
(define-fun report_safety () Bool (=> (> c0ea3a1f2_collateral_math_value c0ea3a1f2_threshold_math_value)
    (not c0ea3a1f2_lt_result)))
(define-fun report_effects () Bool (and (> c0ea3a1f2_collateral_math_value c0ea3a1f2_threshold_math_value)
     (not (not c0ea3a1f2_lt_result))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
