; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c5bc20dbd_equal_exponents_branch_reached () Bool)
(declare-fun c5bc20dbd_le_result () Bool)
(declare-fun c5bc20dbd_not_gt_result () Bool)
(declare-fun c5bc20dbd_values_mathematically_equal () Bool)
(assert
 (= c5bc20dbd_equal_exponents_branch_reached c5bc20dbd_equal_exponents_branch_reached))
(assert
 (= c5bc20dbd_le_result c5bc20dbd_le_result))
(assert
 (= c5bc20dbd_not_gt_result c5bc20dbd_not_gt_result))
(assert
 (= c5bc20dbd_values_mathematically_equal c5bc20dbd_values_mathematically_equal))
(define-fun report_preconditions () Bool (and c5bc20dbd_values_mathematically_equal
     c5bc20dbd_equal_exponents_branch_reached))
(define-fun report_safety () Bool (=> (and c5bc20dbd_values_mathematically_equal
         c5bc20dbd_equal_exponents_branch_reached)
    (= c5bc20dbd_le_result c5bc20dbd_not_gt_result)))
(define-fun report_effects () Bool (and c5bc20dbd_values_mathematically_equal
     c5bc20dbd_equal_exponents_branch_reached
     (not (= c5bc20dbd_le_result c5bc20dbd_not_gt_result))))
(assert report_preconditions)
(check-sat)
(get-model)
