; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4e0cf139_dynamic_fee_accepted () Bool)
(declare-fun c4e0cf139_dynamic_fee_value () Int)
(declare-fun c4e0cf139_factory_fee_threshold () Int)
(assert
 (= c4e0cf139_dynamic_fee_accepted c4e0cf139_dynamic_fee_accepted))
(assert
 (= c4e0cf139_dynamic_fee_value c4e0cf139_dynamic_fee_value))
(assert
 (= c4e0cf139_factory_fee_threshold c4e0cf139_factory_fee_threshold))
(define-fun report_preconditions () Bool (and (< 100000 c4e0cf139_dynamic_fee_value)
     (= 100000 c4e0cf139_factory_fee_threshold)))
(define-fun report_safety () Bool (=> (not c4e0cf139_dynamic_fee_accepted)
    (=> (and (< 100000 c4e0cf139_dynamic_fee_value)
             (= 100000 c4e0cf139_factory_fee_threshold))
        c4e0cf139_dynamic_fee_accepted)))
(define-fun report_effects () Bool (and (not c4e0cf139_dynamic_fee_accepted)
     (< 100000 c4e0cf139_dynamic_fee_value)
     (= 100000 c4e0cf139_factory_fee_threshold)
     (not c4e0cf139_dynamic_fee_accepted)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
