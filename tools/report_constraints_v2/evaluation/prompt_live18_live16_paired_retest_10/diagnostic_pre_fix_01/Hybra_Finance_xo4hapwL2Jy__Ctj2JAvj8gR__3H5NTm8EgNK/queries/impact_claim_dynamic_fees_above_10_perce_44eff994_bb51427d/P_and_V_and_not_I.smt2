; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c043e4e3b_dynamic_fee_rejected () Bool)
(declare-fun c043e4e3b_dynamic_fee_value () Int)
(declare-fun c043e4e3b_factory_fee_cap () Int)
(declare-fun c043e4e3b_module_max_fee_cap () Int)
(assert
 (= c043e4e3b_dynamic_fee_rejected c043e4e3b_dynamic_fee_rejected))
(assert
 (= c043e4e3b_dynamic_fee_value c043e4e3b_dynamic_fee_value))
(assert
 (= c043e4e3b_factory_fee_cap c043e4e3b_factory_fee_cap))
(assert
 (= c043e4e3b_module_max_fee_cap c043e4e3b_module_max_fee_cap))
(define-fun report_preconditions () Bool (and (< 100000 c043e4e3b_dynamic_fee_value)
     (= 100000 c043e4e3b_factory_fee_cap)))
(define-fun report_safety () Bool (=> (and (< 100000 c043e4e3b_dynamic_fee_value) c043e4e3b_dynamic_fee_rejected)
    (=> (and (< 100000 c043e4e3b_dynamic_fee_value)
             (<= c043e4e3b_dynamic_fee_value c043e4e3b_module_max_fee_cap))
        (not c043e4e3b_dynamic_fee_rejected))))
(define-fun report_effects () Bool (and (< 100000 c043e4e3b_dynamic_fee_value)
     c043e4e3b_dynamic_fee_rejected
     (< 100000 c043e4e3b_dynamic_fee_value)
     (<= c043e4e3b_dynamic_fee_value c043e4e3b_module_max_fee_cap)
     (not (not c043e4e3b_dynamic_fee_rejected))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
