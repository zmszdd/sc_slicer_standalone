; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ccdb15d53_dynamic_fee_value () Int)
(declare-fun ccdb15d53_fee_accepted_by_factory () Bool)
(declare-fun ccdb15d53_max_fee_cap () Int)
(assert
 (= ccdb15d53_dynamic_fee_value ccdb15d53_dynamic_fee_value))
(assert
 (= ccdb15d53_fee_accepted_by_factory ccdb15d53_fee_accepted_by_factory))
(assert
 (= ccdb15d53_max_fee_cap ccdb15d53_max_fee_cap))
(define-fun report_preconditions () Bool (and (< 100000 ccdb15d53_dynamic_fee_value) (= 500000 ccdb15d53_max_fee_cap)))
(define-fun report_safety () Bool (=> (<= ccdb15d53_dynamic_fee_value ccdb15d53_max_fee_cap)
    (=> (and (< 100000 ccdb15d53_dynamic_fee_value)
             (= 500000 ccdb15d53_max_fee_cap)
             (<= ccdb15d53_dynamic_fee_value ccdb15d53_max_fee_cap))
        ccdb15d53_fee_accepted_by_factory)))
(define-fun report_effects () Bool (and (<= ccdb15d53_dynamic_fee_value ccdb15d53_max_fee_cap)
     (< 100000 ccdb15d53_dynamic_fee_value)
     (= 500000 ccdb15d53_max_fee_cap)
     (<= ccdb15d53_dynamic_fee_value ccdb15d53_max_fee_cap)
     (not ccdb15d53_fee_accepted_by_factory)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
