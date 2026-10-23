; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0ab5cf3e_dynamic_fee_accepted () Bool)
(declare-fun c0ab5cf3e_dynamic_fee_value () Int)
(declare-fun c0ab5cf3e_falls_back_to_basic_tick_spacing_fees () Bool)
(declare-fun c0ab5cf3e_max_fee_cap () Int)
(assert
 (= c0ab5cf3e_dynamic_fee_accepted c0ab5cf3e_dynamic_fee_accepted))
(assert
 (= c0ab5cf3e_dynamic_fee_value c0ab5cf3e_dynamic_fee_value))
(assert
 (= c0ab5cf3e_falls_back_to_basic_tick_spacing_fees c0ab5cf3e_falls_back_to_basic_tick_spacing_fees))
(assert
 (= c0ab5cf3e_max_fee_cap c0ab5cf3e_max_fee_cap))
(define-fun report_preconditions () Bool (< 100000 c0ab5cf3e_dynamic_fee_value))
(define-fun report_safety () Bool (=> c0ab5cf3e_falls_back_to_basic_tick_spacing_fees
    (=> (and (< 100000 c0ab5cf3e_dynamic_fee_value)
             (<= c0ab5cf3e_dynamic_fee_value c0ab5cf3e_max_fee_cap))
        c0ab5cf3e_dynamic_fee_accepted)))
(define-fun report_effects () Bool (and c0ab5cf3e_falls_back_to_basic_tick_spacing_fees
     (< 100000 c0ab5cf3e_dynamic_fee_value)
     (<= c0ab5cf3e_dynamic_fee_value c0ab5cf3e_max_fee_cap)
     (not c0ab5cf3e_dynamic_fee_accepted)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
