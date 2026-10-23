; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8913a0f1_amount_is_base_true () Bool)
(declare-fun c8913a0f1_amount_not_divisible_by_lot () Bool)
(declare-fun c8913a0f1_dust_tolerance_guarantee_violated_observed () Bool)
(assert
 (= c8913a0f1_amount_is_base_true c8913a0f1_amount_is_base_true))
(assert
 (= c8913a0f1_amount_not_divisible_by_lot c8913a0f1_amount_not_divisible_by_lot))
(assert
 (= c8913a0f1_dust_tolerance_guarantee_violated_observed c8913a0f1_dust_tolerance_guarantee_violated_observed))
(define-fun report_preconditions () Bool (and c8913a0f1_amount_is_base_true c8913a0f1_amount_not_divisible_by_lot))
(define-fun report_safety () Bool (=> (and c8913a0f1_amount_is_base_true c8913a0f1_amount_not_divisible_by_lot)
    (not c8913a0f1_dust_tolerance_guarantee_violated_observed)))
(define-fun report_effects () Bool (and c8913a0f1_amount_is_base_true
     c8913a0f1_amount_not_divisible_by_lot
     (not (not c8913a0f1_dust_tolerance_guarantee_violated_observed))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
