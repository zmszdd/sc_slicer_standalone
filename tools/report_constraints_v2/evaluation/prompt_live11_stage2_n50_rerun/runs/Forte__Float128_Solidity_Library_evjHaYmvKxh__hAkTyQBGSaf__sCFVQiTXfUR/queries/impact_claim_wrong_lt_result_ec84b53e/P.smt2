; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c99f79a13_lt_result () Bool)
(declare-fun c99f79a13_pf_collateral_math_value () Int)
(declare-fun c99f79a13_pf_threshold_math_value () Int)
(assert
 (= c99f79a13_lt_result c99f79a13_lt_result))
(assert
 (= c99f79a13_pf_collateral_math_value c99f79a13_pf_collateral_math_value))
(assert
 (= c99f79a13_pf_threshold_math_value c99f79a13_pf_threshold_math_value))
(define-fun report_preconditions () Bool (and (= 10 c99f79a13_pf_threshold_math_value)
     (= 1000 c99f79a13_pf_collateral_math_value)
     (> c99f79a13_pf_collateral_math_value c99f79a13_pf_threshold_math_value)))
(define-fun report_safety () Bool (=> (> c99f79a13_pf_collateral_math_value c99f79a13_pf_threshold_math_value)
    (not c99f79a13_lt_result)))
(define-fun report_effects () Bool (and (> c99f79a13_pf_collateral_math_value c99f79a13_pf_threshold_math_value)
     (not (not c99f79a13_lt_result))))
(assert report_preconditions)
(check-sat)
(get-model)
