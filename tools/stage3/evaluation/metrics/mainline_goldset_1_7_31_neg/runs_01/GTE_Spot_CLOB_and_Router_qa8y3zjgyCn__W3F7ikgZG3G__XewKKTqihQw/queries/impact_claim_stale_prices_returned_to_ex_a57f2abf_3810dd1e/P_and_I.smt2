; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c78a5d009_external_systems_rely_on_gettob () Bool)
(declare-fun c78a5d009_gettob_returns_expired_derived_price () Bool)
(declare-fun c78a5d009_gettob_returns_live_derived_price () Bool)
(declare-fun c78a5d009_gettob_returns_price_derived_from_expired_orders () Bool)
(assert
 (= c78a5d009_external_systems_rely_on_gettob c78a5d009_external_systems_rely_on_gettob))
(assert
 (= c78a5d009_gettob_returns_expired_derived_price c78a5d009_gettob_returns_expired_derived_price))
(assert
 (= c78a5d009_gettob_returns_live_derived_price c78a5d009_gettob_returns_live_derived_price))
(assert
 (= c78a5d009_gettob_returns_price_derived_from_expired_orders c78a5d009_gettob_returns_price_derived_from_expired_orders))
(define-fun report_preconditions () Bool c78a5d009_external_systems_rely_on_gettob)
(define-fun report_safety () Bool (=> c78a5d009_external_systems_rely_on_gettob
    (= c78a5d009_gettob_returns_expired_derived_price
       c78a5d009_gettob_returns_live_derived_price)))
(define-fun report_effects () Bool (and c78a5d009_external_systems_rely_on_gettob
     (not (= c78a5d009_gettob_returns_expired_derived_price
             c78a5d009_gettob_returns_live_derived_price))
     c78a5d009_gettob_returns_price_derived_from_expired_orders
     c78a5d009_gettob_returns_price_derived_from_expired_orders))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
