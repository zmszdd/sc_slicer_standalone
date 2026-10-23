; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c081514f2_dynamic_fee_value () Int)
(declare-fun c081514f2_factory_fee_reject_threshold () Int)
(declare-fun c081514f2_fee_accepted_by_factory () Bool)
(declare-fun c081514f2_max_fee_cap () Int)
(assert
 (= c081514f2_dynamic_fee_value c081514f2_dynamic_fee_value))
(assert
 (= c081514f2_factory_fee_reject_threshold c081514f2_factory_fee_reject_threshold))
(assert
 (= c081514f2_fee_accepted_by_factory c081514f2_fee_accepted_by_factory))
(assert
 (= c081514f2_max_fee_cap c081514f2_max_fee_cap))
(define-fun report_preconditions () Bool (and (> c081514f2_dynamic_fee_value c081514f2_factory_fee_reject_threshold)
     (> c081514f2_dynamic_fee_value c081514f2_factory_fee_reject_threshold)))
(define-fun report_safety () Bool (=> (not c081514f2_fee_accepted_by_factory)
    (=> (and (> c081514f2_dynamic_fee_value
                c081514f2_factory_fee_reject_threshold)
             (<= c081514f2_dynamic_fee_value c081514f2_max_fee_cap))
        c081514f2_fee_accepted_by_factory)))
(define-fun report_effects () Bool (and (not c081514f2_fee_accepted_by_factory)
     (> c081514f2_dynamic_fee_value c081514f2_factory_fee_reject_threshold)
     (<= c081514f2_dynamic_fee_value c081514f2_max_fee_cap)
     (not c081514f2_fee_accepted_by_factory)))
