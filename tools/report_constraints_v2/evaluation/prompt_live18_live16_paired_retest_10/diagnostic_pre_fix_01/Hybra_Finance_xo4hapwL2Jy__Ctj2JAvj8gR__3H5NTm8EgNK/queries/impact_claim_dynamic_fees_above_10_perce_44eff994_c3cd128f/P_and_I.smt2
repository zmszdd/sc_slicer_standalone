; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd89ea011_dynamic_fee_rejected () Bool)
(declare-fun cd89ea011_dynamic_fee_value () Int)
(declare-fun cd89ea011_factory_fee_threshold () Int)
(assert
 (= cd89ea011_dynamic_fee_rejected cd89ea011_dynamic_fee_rejected))
(assert
 (= cd89ea011_dynamic_fee_value cd89ea011_dynamic_fee_value))
(assert
 (= cd89ea011_factory_fee_threshold cd89ea011_factory_fee_threshold))
(define-fun report_preconditions () Bool (and (< 100000 cd89ea011_dynamic_fee_value)
     (= 100000 cd89ea011_factory_fee_threshold)))
(define-fun report_safety () Bool (=> (and (< 100000 cd89ea011_dynamic_fee_value) cd89ea011_dynamic_fee_rejected)
    (=> (< 100000 cd89ea011_dynamic_fee_value)
        (not cd89ea011_dynamic_fee_rejected))))
(define-fun report_effects () Bool (and (< 100000 cd89ea011_dynamic_fee_value)
     cd89ea011_dynamic_fee_rejected
     (< 100000 cd89ea011_dynamic_fee_value)
     (not (not cd89ea011_dynamic_fee_rejected))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
