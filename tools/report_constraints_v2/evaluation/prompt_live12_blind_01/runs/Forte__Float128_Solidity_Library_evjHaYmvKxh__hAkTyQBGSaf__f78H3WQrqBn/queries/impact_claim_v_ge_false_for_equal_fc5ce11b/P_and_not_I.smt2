; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca6b0edb8_floats_equal_value () Bool)
(declare-fun ca6b0edb8_ge_returns_false_for_equal () Bool)
(declare-fun ca6b0edb8_one_float_has_l_mantissa () Bool)
(assert
 (= ca6b0edb8_floats_equal_value ca6b0edb8_floats_equal_value))
(assert
 (= ca6b0edb8_ge_returns_false_for_equal ca6b0edb8_ge_returns_false_for_equal))
(assert
 (= ca6b0edb8_one_float_has_l_mantissa ca6b0edb8_one_float_has_l_mantissa))
(define-fun report_preconditions () Bool (and ca6b0edb8_one_float_has_l_mantissa ca6b0edb8_floats_equal_value))
(define-fun report_safety () Bool (=> (and ca6b0edb8_one_float_has_l_mantissa ca6b0edb8_floats_equal_value)
    (not ca6b0edb8_ge_returns_false_for_equal)))
(define-fun report_effects () Bool (and ca6b0edb8_one_float_has_l_mantissa
     ca6b0edb8_floats_equal_value
     (not (not ca6b0edb8_ge_returns_false_for_equal))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
