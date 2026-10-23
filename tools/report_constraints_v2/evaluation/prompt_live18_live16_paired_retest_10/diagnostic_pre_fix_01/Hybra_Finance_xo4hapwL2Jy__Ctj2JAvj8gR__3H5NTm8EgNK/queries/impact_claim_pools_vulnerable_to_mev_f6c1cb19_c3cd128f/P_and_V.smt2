; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0be3329d_dynamic_fee () Int)
(declare-fun c0be3329d_factory_fee_threshold () Int)
(declare-fun c0be3329d_high_volatility () Bool)
(declare-fun c0be3329d_max_fee_cap () Int)
(assert
 (= c0be3329d_dynamic_fee c0be3329d_dynamic_fee))
(assert
 (= c0be3329d_factory_fee_threshold c0be3329d_factory_fee_threshold))
(assert
 (= c0be3329d_high_volatility c0be3329d_high_volatility))
(assert
 (= c0be3329d_max_fee_cap c0be3329d_max_fee_cap))
(define-fun report_preconditions () Bool (and (= 500000 c0be3329d_max_fee_cap)
     (= 100000 c0be3329d_factory_fee_threshold)))
(define-fun report_safety () Bool (=> c0be3329d_high_volatility
    (=> c0be3329d_high_volatility
        (<= c0be3329d_dynamic_fee c0be3329d_max_fee_cap))))
(define-fun report_effects () Bool (and c0be3329d_high_volatility
     c0be3329d_high_volatility
     (not (<= c0be3329d_dynamic_fee c0be3329d_max_fee_cap))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
