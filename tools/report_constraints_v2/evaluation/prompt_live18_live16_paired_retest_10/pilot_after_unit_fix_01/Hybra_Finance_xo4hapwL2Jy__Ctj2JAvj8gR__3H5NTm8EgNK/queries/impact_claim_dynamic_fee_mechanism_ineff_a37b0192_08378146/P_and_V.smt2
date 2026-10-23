; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ccdb15d53_dynamic_fee_value () Int)
(declare-fun ccdb15d53_factory_fee_reject_threshold () Int)
(declare-fun ccdb15d53_fee_accepted_and_applied () Bool)
(declare-fun ccdb15d53_max_fee_cap () Int)
(assert
 (= ccdb15d53_dynamic_fee_value ccdb15d53_dynamic_fee_value))
(assert
 (= ccdb15d53_factory_fee_reject_threshold ccdb15d53_factory_fee_reject_threshold))
(assert
 (= ccdb15d53_fee_accepted_and_applied ccdb15d53_fee_accepted_and_applied))
(assert
 (= ccdb15d53_max_fee_cap ccdb15d53_max_fee_cap))
(define-fun report_preconditions () Bool (and (= 500000 ccdb15d53_max_fee_cap)
     (= 100000 ccdb15d53_factory_fee_reject_threshold)))
(define-fun report_safety () Bool (=> (> ccdb15d53_dynamic_fee_value ccdb15d53_factory_fee_reject_threshold)
    (=> (and (<= ccdb15d53_dynamic_fee_value ccdb15d53_max_fee_cap)
             (> ccdb15d53_dynamic_fee_value
                ccdb15d53_factory_fee_reject_threshold))
        ccdb15d53_fee_accepted_and_applied)))
(define-fun report_effects () Bool (and (> ccdb15d53_dynamic_fee_value ccdb15d53_factory_fee_reject_threshold)
     (<= ccdb15d53_dynamic_fee_value ccdb15d53_max_fee_cap)
     (> ccdb15d53_dynamic_fee_value ccdb15d53_factory_fee_reject_threshold)
     (not ccdb15d53_fee_accepted_and_applied)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
