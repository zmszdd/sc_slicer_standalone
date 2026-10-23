; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc2904756_exponents_equal () Bool)
(declare-fun cc2904756_le_result_consistent () Bool)
(declare-fun cc2904756_math_equal_diff_repr () Bool)
(assert
 (= cc2904756_exponents_equal cc2904756_exponents_equal))
(assert
 (= cc2904756_le_result_consistent cc2904756_le_result_consistent))
(assert
 (= cc2904756_math_equal_diff_repr cc2904756_math_equal_diff_repr))
(define-fun report_preconditions () Bool (and cc2904756_exponents_equal cc2904756_math_equal_diff_repr))
(define-fun report_safety () Bool (=> (and cc2904756_exponents_equal cc2904756_math_equal_diff_repr)
    cc2904756_le_result_consistent))
(define-fun report_effects () Bool (and cc2904756_exponents_equal
     cc2904756_math_equal_diff_repr
     (not cc2904756_le_result_consistent)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
