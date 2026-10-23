; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c925cf983_financial_loss_unbounded () Bool)
(declare-fun c925cf983_total_assets_before_first_fulfillment () Int)
(declare-fun c925cf983_total_supply_after_constructor () Int)
(declare-fun c925cf983_underlying_assets_after_constructor () Int)
(assert
 (= c925cf983_financial_loss_unbounded c925cf983_financial_loss_unbounded))
(assert
 (= c925cf983_total_assets_before_first_fulfillment c925cf983_total_assets_before_first_fulfillment))
(assert
 (= c925cf983_total_supply_after_constructor c925cf983_total_supply_after_constructor))
(assert
 (= c925cf983_underlying_assets_after_constructor c925cf983_underlying_assets_after_constructor))
(define-fun report_preconditions () Bool (and (= 1000000 c925cf983_total_supply_after_constructor)
     (= 1 c925cf983_total_assets_before_first_fulfillment)))
(define-fun report_safety () Bool (=> (= 0 c925cf983_underlying_assets_after_constructor)
    (= 0 c925cf983_total_supply_after_constructor)))
(define-fun report_effects () Bool c925cf983_financial_loss_unbounded)
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
