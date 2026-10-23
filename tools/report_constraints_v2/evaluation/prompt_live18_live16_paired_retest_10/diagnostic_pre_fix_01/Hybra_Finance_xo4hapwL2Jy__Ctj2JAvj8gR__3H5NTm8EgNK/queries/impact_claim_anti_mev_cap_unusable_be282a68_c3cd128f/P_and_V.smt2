; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb2395121_dynamic_fee () Int)
(declare-fun cb2395121_factory_fee_threshold () Int)
(declare-fun cb2395121_max_fee_cap () Int)
(assert
 (= cb2395121_dynamic_fee cb2395121_dynamic_fee))
(assert
 (= cb2395121_factory_fee_threshold cb2395121_factory_fee_threshold))
(assert
 (= cb2395121_max_fee_cap cb2395121_max_fee_cap))
(define-fun report_preconditions () Bool (and (= 500000 cb2395121_max_fee_cap)
     (= 100000 cb2395121_factory_fee_threshold)))
(define-fun report_safety () Bool (=> (> cb2395121_dynamic_fee cb2395121_factory_fee_threshold)
    (=> (<= cb2395121_dynamic_fee cb2395121_max_fee_cap)
        (<= cb2395121_dynamic_fee cb2395121_max_fee_cap))))
(define-fun report_effects () Bool (and (> cb2395121_dynamic_fee cb2395121_factory_fee_threshold)
     (<= cb2395121_dynamic_fee cb2395121_max_fee_cap)
     (not (<= cb2395121_dynamic_fee cb2395121_max_fee_cap))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
