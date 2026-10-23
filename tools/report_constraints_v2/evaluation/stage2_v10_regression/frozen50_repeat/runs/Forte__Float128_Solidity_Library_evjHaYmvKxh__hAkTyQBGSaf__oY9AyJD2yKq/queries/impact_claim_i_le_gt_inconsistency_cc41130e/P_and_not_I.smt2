; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c5bc20dbd_exponents_equal () Bool)
(declare-fun c5bc20dbd_le_gt_consistent () Bool)
(declare-fun c5bc20dbd_math_equal_diff_repr () Bool)
(assert
 (= c5bc20dbd_exponents_equal c5bc20dbd_exponents_equal))
(assert
 (= c5bc20dbd_le_gt_consistent c5bc20dbd_le_gt_consistent))
(assert
 (= c5bc20dbd_math_equal_diff_repr c5bc20dbd_math_equal_diff_repr))
(define-fun report_preconditions () Bool (and c5bc20dbd_exponents_equal c5bc20dbd_math_equal_diff_repr))
(define-fun report_safety () Bool (=> (and c5bc20dbd_exponents_equal c5bc20dbd_math_equal_diff_repr)
    c5bc20dbd_le_gt_consistent))
(define-fun report_effects () Bool (and c5bc20dbd_exponents_equal
     c5bc20dbd_math_equal_diff_repr
     (not c5bc20dbd_le_gt_consistent)))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
