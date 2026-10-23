; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c28a31543_share_price_integration_correct () Bool)
(declare-fun c28a31543_total_assets_before_first_fulfilment () Int)
(declare-fun c28a31543_total_supply_after_constructor () Int)
(declare-fun c28a31543_underlying_assets_held_initially () Int)
(assert
 (= c28a31543_share_price_integration_correct c28a31543_share_price_integration_correct))
(assert
 (= c28a31543_total_assets_before_first_fulfilment c28a31543_total_assets_before_first_fulfilment))
(assert
 (= c28a31543_total_supply_after_constructor c28a31543_total_supply_after_constructor))
(assert
 (= c28a31543_underlying_assets_held_initially c28a31543_underlying_assets_held_initially))
(define-fun report_preconditions () Bool (and (= 1000000 c28a31543_total_supply_after_constructor)
     (= 0 c28a31543_underlying_assets_held_initially)
     (= 1 c28a31543_total_assets_before_first_fulfilment)))
(define-fun report_safety () Bool (=> (not c28a31543_share_price_integration_correct)
    (=> (and (= 1000000 c28a31543_total_supply_after_constructor)
             (= 0 c28a31543_underlying_assets_held_initially)
             (= 1 c28a31543_total_assets_before_first_fulfilment))
        (= c28a31543_share_price_integration_correct
           c28a31543_share_price_integration_correct))))
(define-fun report_effects () Bool (and (not c28a31543_share_price_integration_correct)
     (= 1000000 c28a31543_total_supply_after_constructor)
     (= 0 c28a31543_underlying_assets_held_initially)
     (= 1 c28a31543_total_assets_before_first_fulfilment)
     (not (= c28a31543_share_price_integration_correct
             c28a31543_share_price_integration_correct))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
