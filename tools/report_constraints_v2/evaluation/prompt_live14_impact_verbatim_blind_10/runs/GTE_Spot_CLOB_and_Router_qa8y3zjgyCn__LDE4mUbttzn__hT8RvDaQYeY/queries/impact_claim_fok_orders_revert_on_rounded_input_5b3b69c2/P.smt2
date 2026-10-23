; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c5754ac8c_amount_is_base_true () Bool)
(declare-fun c5754ac8c_amount_not_divisible_by_lot () Bool)
(declare-fun c5754ac8c_fok_fill_reverted () Bool)
(assert
 (= c5754ac8c_amount_is_base_true c5754ac8c_amount_is_base_true))
(assert
 (= c5754ac8c_amount_not_divisible_by_lot c5754ac8c_amount_not_divisible_by_lot))
(assert
 (= c5754ac8c_fok_fill_reverted c5754ac8c_fok_fill_reverted))
(define-fun report_preconditions () Bool (and c5754ac8c_amount_is_base_true c5754ac8c_amount_not_divisible_by_lot))
(define-fun report_safety () Bool (=> (and c5754ac8c_amount_is_base_true c5754ac8c_amount_not_divisible_by_lot)
    (not c5754ac8c_fok_fill_reverted)))
(define-fun report_effects () Bool (and c5754ac8c_amount_is_base_true
     c5754ac8c_amount_not_divisible_by_lot
     (not (not c5754ac8c_fok_fill_reverted))))
(assert report_preconditions)
(check-sat)
(get-model)
