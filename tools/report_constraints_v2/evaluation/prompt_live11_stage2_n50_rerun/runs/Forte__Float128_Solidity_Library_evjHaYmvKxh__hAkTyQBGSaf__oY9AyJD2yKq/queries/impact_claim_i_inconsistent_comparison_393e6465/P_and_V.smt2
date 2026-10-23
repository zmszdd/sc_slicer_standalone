; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc2904756_equal_exponents_branch_reached () Bool)
(declare-fun cc2904756_le_result_ab () Bool)
(declare-fun cc2904756_le_result_ba () Bool)
(declare-fun cc2904756_values_mathematically_equal () Bool)
(assert
 (= cc2904756_equal_exponents_branch_reached cc2904756_equal_exponents_branch_reached))
(assert
 (= cc2904756_le_result_ab cc2904756_le_result_ab))
(assert
 (= cc2904756_le_result_ba cc2904756_le_result_ba))
(assert
 (= cc2904756_values_mathematically_equal cc2904756_values_mathematically_equal))
(define-fun report_preconditions () Bool (and cc2904756_values_mathematically_equal
     cc2904756_equal_exponents_branch_reached))
(define-fun report_safety () Bool (=> (and cc2904756_values_mathematically_equal
         cc2904756_equal_exponents_branch_reached)
    (= cc2904756_le_result_ab cc2904756_le_result_ba)))
(define-fun report_effects () Bool (and cc2904756_values_mathematically_equal
     cc2904756_equal_exponents_branch_reached
     (not (= cc2904756_le_result_ab cc2904756_le_result_ba))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
