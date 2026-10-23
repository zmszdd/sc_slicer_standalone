; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cf85b8eca_amount_is_base_true () Bool)
(declare-fun cf85b8eca_amount_not_divisible_by_lot () Bool)
(declare-fun cf85b8eca_fok_behavior_unpredictable_observed () Bool)
(declare-fun cf85b8eca_fok_fill_completed_without_revert () Bool)
(assert
 (= cf85b8eca_amount_is_base_true cf85b8eca_amount_is_base_true))
(assert
 (= cf85b8eca_amount_not_divisible_by_lot cf85b8eca_amount_not_divisible_by_lot))
(assert
 (= cf85b8eca_fok_behavior_unpredictable_observed cf85b8eca_fok_behavior_unpredictable_observed))
(assert
 (= cf85b8eca_fok_fill_completed_without_revert cf85b8eca_fok_fill_completed_without_revert))
(define-fun report_preconditions () Bool (and cf85b8eca_amount_is_base_true cf85b8eca_amount_not_divisible_by_lot))
(define-fun report_safety () Bool (=> (and cf85b8eca_amount_is_base_true cf85b8eca_amount_not_divisible_by_lot)
    (and cf85b8eca_fok_fill_completed_without_revert
         (not cf85b8eca_fok_behavior_unpredictable_observed))))
(define-fun report_effects () Bool (and cf85b8eca_amount_is_base_true
     cf85b8eca_amount_not_divisible_by_lot
     (not (and cf85b8eca_fok_fill_completed_without_revert
               (not cf85b8eca_fok_behavior_unpredictable_observed)))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
