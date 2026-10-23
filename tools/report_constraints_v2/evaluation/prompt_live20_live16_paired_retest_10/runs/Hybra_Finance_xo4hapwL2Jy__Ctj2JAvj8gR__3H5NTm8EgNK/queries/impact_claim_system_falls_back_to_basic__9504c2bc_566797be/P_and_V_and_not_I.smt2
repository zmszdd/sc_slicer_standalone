; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbc08b9d9_dynamic_fee_applied () Bool)
(declare-fun cbc08b9d9_falls_back_to_basic_tick_spacing_fees () Bool)
(declare-fun cbc08b9d9_max_fee_cap () Int)
(assert
 (= cbc08b9d9_dynamic_fee_applied cbc08b9d9_dynamic_fee_applied))
(assert
 (= cbc08b9d9_falls_back_to_basic_tick_spacing_fees cbc08b9d9_falls_back_to_basic_tick_spacing_fees))
(assert
 (= cbc08b9d9_max_fee_cap cbc08b9d9_max_fee_cap))
(define-fun report_preconditions () Bool (= 500000 cbc08b9d9_max_fee_cap))
(define-fun report_safety () Bool (=> cbc08b9d9_dynamic_fee_applied
    (not cbc08b9d9_falls_back_to_basic_tick_spacing_fees)))
(define-fun report_effects () Bool (and cbc08b9d9_falls_back_to_basic_tick_spacing_fees
     cbc08b9d9_falls_back_to_basic_tick_spacing_fees))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
