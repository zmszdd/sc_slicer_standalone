; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd889750f_dynamic_fee_value () Int)
(declare-fun cd889750f_factory_fee_reject_threshold () Int)
(declare-fun cd889750f_fee_accepted () Bool)
(declare-fun cd889750f_max_fee_cap () Int)
(assert
 (= cd889750f_dynamic_fee_value cd889750f_dynamic_fee_value))
(assert
 (= cd889750f_factory_fee_reject_threshold cd889750f_factory_fee_reject_threshold))
(assert
 (= cd889750f_fee_accepted cd889750f_fee_accepted))
(assert
 (= cd889750f_max_fee_cap cd889750f_max_fee_cap))
(define-fun report_preconditions () Bool (and (= 500000 cd889750f_max_fee_cap)
     (= 100000 cd889750f_factory_fee_reject_threshold)))
(define-fun report_safety () Bool (=> (> cd889750f_dynamic_fee_value cd889750f_factory_fee_reject_threshold)
    (=> (and (<= cd889750f_dynamic_fee_value cd889750f_max_fee_cap)
             (> cd889750f_dynamic_fee_value
                cd889750f_factory_fee_reject_threshold))
        cd889750f_fee_accepted)))
(define-fun report_effects () Bool (and (> cd889750f_dynamic_fee_value cd889750f_factory_fee_reject_threshold)
     (<= cd889750f_dynamic_fee_value cd889750f_max_fee_cap)
     (> cd889750f_dynamic_fee_value cd889750f_factory_fee_reject_threshold)
     (not cd889750f_fee_accepted)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
