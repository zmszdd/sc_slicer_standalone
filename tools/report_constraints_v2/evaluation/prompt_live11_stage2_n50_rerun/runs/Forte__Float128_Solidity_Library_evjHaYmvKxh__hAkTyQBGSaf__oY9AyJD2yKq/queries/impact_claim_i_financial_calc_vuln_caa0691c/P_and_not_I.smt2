; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c86e2dae7_equal_exponents_branch_reached () Bool)
(declare-fun c86e2dae7_le_result_consistent () Bool)
(declare-fun c86e2dae7_values_mathematically_equal () Bool)
(assert
 (= c86e2dae7_equal_exponents_branch_reached c86e2dae7_equal_exponents_branch_reached))
(assert
 (= c86e2dae7_le_result_consistent c86e2dae7_le_result_consistent))
(assert
 (= c86e2dae7_values_mathematically_equal c86e2dae7_values_mathematically_equal))
(define-fun report_preconditions () Bool (and c86e2dae7_values_mathematically_equal
     c86e2dae7_equal_exponents_branch_reached))
(define-fun report_safety () Bool (=> (and c86e2dae7_values_mathematically_equal
         c86e2dae7_equal_exponents_branch_reached)
    c86e2dae7_le_result_consistent))
(define-fun report_effects () Bool (and c86e2dae7_values_mathematically_equal
     c86e2dae7_equal_exponents_branch_reached
     (not c86e2dae7_le_result_consistent)))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
