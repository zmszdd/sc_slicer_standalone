; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cdcb2f3c6_exponents_equal () Bool)
(declare-fun cdcb2f3c6_financial_calc_exact_comparison () Bool)
(declare-fun cdcb2f3c6_le_consistent_for_equal_values () Bool)
(declare-fun cdcb2f3c6_math_equal_diff_repr () Bool)
(assert
 (= cdcb2f3c6_exponents_equal cdcb2f3c6_exponents_equal))
(assert
 (= cdcb2f3c6_financial_calc_exact_comparison cdcb2f3c6_financial_calc_exact_comparison))
(assert
 (= cdcb2f3c6_le_consistent_for_equal_values cdcb2f3c6_le_consistent_for_equal_values))
(assert
 (= cdcb2f3c6_math_equal_diff_repr cdcb2f3c6_math_equal_diff_repr))
(define-fun report_preconditions () Bool (and cdcb2f3c6_exponents_equal cdcb2f3c6_math_equal_diff_repr))
(define-fun report_safety () Bool (=> (and cdcb2f3c6_exponents_equal
         cdcb2f3c6_math_equal_diff_repr
         cdcb2f3c6_financial_calc_exact_comparison)
    cdcb2f3c6_le_consistent_for_equal_values))
(define-fun report_effects () Bool (and cdcb2f3c6_exponents_equal
     cdcb2f3c6_math_equal_diff_repr
     cdcb2f3c6_financial_calc_exact_comparison
     (not cdcb2f3c6_le_consistent_for_equal_values)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
