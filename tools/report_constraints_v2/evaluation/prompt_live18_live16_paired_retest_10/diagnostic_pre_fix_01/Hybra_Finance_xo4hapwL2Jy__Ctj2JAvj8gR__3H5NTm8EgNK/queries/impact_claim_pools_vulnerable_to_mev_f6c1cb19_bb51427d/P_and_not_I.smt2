; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c27db107b_dynamic_fee_value () Int)
(declare-fun c27db107b_factory_fee_reject_threshold () Int)
(declare-fun c27db107b_fee_accepted_by_factory () Bool)
(declare-fun c27db107b_high_volatility () Bool)
(declare-fun c27db107b_max_fee_cap () Int)
(assert
 (= c27db107b_dynamic_fee_value c27db107b_dynamic_fee_value))
(assert
 (= c27db107b_factory_fee_reject_threshold c27db107b_factory_fee_reject_threshold))
(assert
 (= c27db107b_fee_accepted_by_factory c27db107b_fee_accepted_by_factory))
(assert
 (= c27db107b_high_volatility c27db107b_high_volatility))
(assert
 (= c27db107b_max_fee_cap c27db107b_max_fee_cap))
(define-fun report_preconditions () Bool (and (= 500000 c27db107b_max_fee_cap)
     (= 100000 c27db107b_factory_fee_reject_threshold)))
(define-fun report_safety () Bool (=> c27db107b_high_volatility
    (=> (and (<= c27db107b_dynamic_fee_value c27db107b_max_fee_cap)
             (> c27db107b_dynamic_fee_value
                c27db107b_factory_fee_reject_threshold))
        c27db107b_fee_accepted_by_factory)))
(define-fun report_effects () Bool (and c27db107b_high_volatility
     (<= c27db107b_dynamic_fee_value c27db107b_max_fee_cap)
     (> c27db107b_dynamic_fee_value c27db107b_factory_fee_reject_threshold)
     (not c27db107b_fee_accepted_by_factory)))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
