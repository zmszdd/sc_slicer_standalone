; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ced15a377_dynamic_fee_accepted () Bool)
(declare-fun ced15a377_dynamic_fee_value () Int)
(declare-fun ced15a377_factory_rejection_threshold () Int)
(declare-fun ced15a377_falls_back_to_basic_tick_spacing_fees () Bool)
(declare-fun ced15a377_max_fee_cap () Int)
(assert
 (= ced15a377_dynamic_fee_accepted ced15a377_dynamic_fee_accepted))
(assert
 (= ced15a377_dynamic_fee_value ced15a377_dynamic_fee_value))
(assert
 (= ced15a377_factory_rejection_threshold ced15a377_factory_rejection_threshold))
(assert
 (= ced15a377_falls_back_to_basic_tick_spacing_fees ced15a377_falls_back_to_basic_tick_spacing_fees))
(assert
 (= ced15a377_max_fee_cap ced15a377_max_fee_cap))
(define-fun report_preconditions () Bool (= 100000 ced15a377_factory_rejection_threshold))
(define-fun report_safety () Bool (=> ced15a377_falls_back_to_basic_tick_spacing_fees
    (=> (and (<= ced15a377_dynamic_fee_value ced15a377_max_fee_cap)
             (> ced15a377_dynamic_fee_value
                ced15a377_factory_rejection_threshold))
        ced15a377_dynamic_fee_accepted)))
(define-fun report_effects () Bool (and ced15a377_falls_back_to_basic_tick_spacing_fees
     (<= ced15a377_dynamic_fee_value ced15a377_max_fee_cap)
     (> ced15a377_dynamic_fee_value ced15a377_factory_rejection_threshold)
     (not ced15a377_dynamic_fee_accepted)))
