; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6f53bf9a_exponents_equal () Bool)
(declare-fun c6f53bf9a_le_gt_consistent () Bool)
(declare-fun c6f53bf9a_values_mathematically_equal () Bool)
(assert
 (= c6f53bf9a_exponents_equal c6f53bf9a_exponents_equal))
(assert
 (= c6f53bf9a_le_gt_consistent c6f53bf9a_le_gt_consistent))
(assert
 (= c6f53bf9a_values_mathematically_equal c6f53bf9a_values_mathematically_equal))
(define-fun report_preconditions () Bool (and c6f53bf9a_exponents_equal c6f53bf9a_values_mathematically_equal))
(define-fun report_safety () Bool (=> (and c6f53bf9a_exponents_equal c6f53bf9a_values_mathematically_equal)
    c6f53bf9a_le_gt_consistent))
(define-fun report_effects () Bool (and c6f53bf9a_exponents_equal
     c6f53bf9a_values_mathematically_equal
     (not c6f53bf9a_le_gt_consistent)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
