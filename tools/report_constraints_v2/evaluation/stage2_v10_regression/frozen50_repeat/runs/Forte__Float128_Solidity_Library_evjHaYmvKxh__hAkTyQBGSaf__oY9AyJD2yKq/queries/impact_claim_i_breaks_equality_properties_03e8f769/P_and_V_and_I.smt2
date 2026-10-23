; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c885c20d4_equality_properties_broken () Bool)
(declare-fun c885c20d4_exponents_equal () Bool)
(declare-fun c885c20d4_math_equal_diff_repr () Bool)
(assert
 (= c885c20d4_equality_properties_broken c885c20d4_equality_properties_broken))
(assert
 (= c885c20d4_exponents_equal c885c20d4_exponents_equal))
(assert
 (= c885c20d4_math_equal_diff_repr c885c20d4_math_equal_diff_repr))
(define-fun report_preconditions () Bool (and c885c20d4_exponents_equal c885c20d4_math_equal_diff_repr))
(define-fun report_safety () Bool (=> (and c885c20d4_exponents_equal c885c20d4_math_equal_diff_repr)
    (not c885c20d4_equality_properties_broken)))
(define-fun report_effects () Bool (and c885c20d4_exponents_equal
     c885c20d4_math_equal_diff_repr
     (not (not c885c20d4_equality_properties_broken))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
