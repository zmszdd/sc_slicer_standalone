; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0ab5cf3e_dynamic_fee_accepted () Bool)
(declare-fun c0ab5cf3e_factory_rejection_threshold () Int)
(declare-fun c0ab5cf3e_falls_back_to_basic_tick_spacing_fees () Bool)
(declare-fun c0ab5cf3e_max_fee_cap () Int)
(declare-fun c0ab5cf3e_swap_fee_value () Int)
(assert
 (= c0ab5cf3e_dynamic_fee_accepted c0ab5cf3e_dynamic_fee_accepted))
(assert
 (= c0ab5cf3e_factory_rejection_threshold c0ab5cf3e_factory_rejection_threshold))
(assert
 (= c0ab5cf3e_falls_back_to_basic_tick_spacing_fees c0ab5cf3e_falls_back_to_basic_tick_spacing_fees))
(assert
 (= c0ab5cf3e_max_fee_cap c0ab5cf3e_max_fee_cap))
(assert
 (= c0ab5cf3e_swap_fee_value c0ab5cf3e_swap_fee_value))
(define-fun report_preconditions () Bool (> c0ab5cf3e_swap_fee_value c0ab5cf3e_factory_rejection_threshold))
(define-fun report_safety () Bool (=> c0ab5cf3e_falls_back_to_basic_tick_spacing_fees
    (=> (and (<= c0ab5cf3e_swap_fee_value c0ab5cf3e_max_fee_cap)
             (> c0ab5cf3e_swap_fee_value c0ab5cf3e_factory_rejection_threshold))
        c0ab5cf3e_dynamic_fee_accepted)))
(define-fun report_effects () Bool (and c0ab5cf3e_falls_back_to_basic_tick_spacing_fees
     (<= c0ab5cf3e_swap_fee_value c0ab5cf3e_max_fee_cap)
     (> c0ab5cf3e_swap_fee_value c0ab5cf3e_factory_rejection_threshold)
     (not c0ab5cf3e_dynamic_fee_accepted)))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
