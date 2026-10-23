; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc228e740_cap_fee_usable () Bool)
(declare-fun cc228e740_factory_fee_reject_threshold () Int)
(declare-fun cc228e740_max_fee_cap () Int)
(assert
 (= cc228e740_cap_fee_usable cc228e740_cap_fee_usable))
(assert
 (= cc228e740_factory_fee_reject_threshold cc228e740_factory_fee_reject_threshold))
(assert
 (= cc228e740_max_fee_cap cc228e740_max_fee_cap))
(define-fun report_preconditions () Bool (and (= 500000 cc228e740_max_fee_cap)
     (= 100000 cc228e740_factory_fee_reject_threshold)))
(define-fun report_safety () Bool (=> (not cc228e740_cap_fee_usable)
    (=> (and (= 500000 cc228e740_max_fee_cap)
             (= 100000 cc228e740_factory_fee_reject_threshold))
        cc228e740_cap_fee_usable)))
(define-fun report_effects () Bool (and (not cc228e740_cap_fee_usable)
     (= 500000 cc228e740_max_fee_cap)
     (= 100000 cc228e740_factory_fee_reject_threshold)
     (not cc228e740_cap_fee_usable)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
