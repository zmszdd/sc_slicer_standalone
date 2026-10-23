; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cedac8269_later_depositors_received_worthless_shares () Bool)
(declare-fun cedac8269_total_assets_before_first_fulfillment () Int)
(declare-fun cedac8269_total_supply_at_constructor () Int)
(assert
 (= cedac8269_later_depositors_received_worthless_shares cedac8269_later_depositors_received_worthless_shares))
(assert
 (= cedac8269_total_assets_before_first_fulfillment cedac8269_total_assets_before_first_fulfillment))
(assert
 (= cedac8269_total_supply_at_constructor cedac8269_total_supply_at_constructor))
(define-fun report_preconditions () Bool (and (= 1000000 cedac8269_total_supply_at_constructor)
     (= 1 cedac8269_total_assets_before_first_fulfillment)))
(define-fun report_safety () Bool (=> (= 1 cedac8269_total_assets_before_first_fulfillment)
    (= 0 cedac8269_total_supply_at_constructor)))
(define-fun report_effects () Bool cedac8269_later_depositors_received_worthless_shares)
(assert report_preconditions)
(assert report_safety)
(check-sat)
