; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c05879e4b_dynamic_fee_value () Int)
(declare-fun c05879e4b_factory_fee_cap () Int)
(declare-fun c05879e4b_fee_rejected () Bool)
(declare-fun c05879e4b_max_fee_cap () Int)
(assert
 (= c05879e4b_dynamic_fee_value c05879e4b_dynamic_fee_value))
(assert
 (= c05879e4b_factory_fee_cap c05879e4b_factory_fee_cap))
(assert
 (= c05879e4b_fee_rejected c05879e4b_fee_rejected))
(assert
 (= c05879e4b_max_fee_cap c05879e4b_max_fee_cap))
(define-fun report_preconditions () Bool (and (< 100000 c05879e4b_dynamic_fee_value)
     (> c05879e4b_dynamic_fee_value c05879e4b_factory_fee_cap)))
(define-fun report_safety () Bool (=> (and (< 100000 c05879e4b_dynamic_fee_value) c05879e4b_fee_rejected)
    (=> (and (<= c05879e4b_dynamic_fee_value c05879e4b_max_fee_cap)
             (< 0 c05879e4b_dynamic_fee_value))
        (not c05879e4b_fee_rejected))))
(define-fun report_effects () Bool (and (< 100000 c05879e4b_dynamic_fee_value)
     c05879e4b_fee_rejected
     (<= c05879e4b_dynamic_fee_value c05879e4b_max_fee_cap)
     (< 0 c05879e4b_dynamic_fee_value)
     (not (not c05879e4b_fee_rejected))))
(assert report_preconditions)
(check-sat)
(get-model)
