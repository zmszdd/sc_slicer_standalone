; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3137c255_assets_to_fulfill_first_deposit () Int)
(declare-fun c3137c255_first_depositor_share_control () Bool)
(declare-fun c3137c255_shares_received_first_deposit () Int)
(declare-fun c3137c255_total_assets_before_first_fulfillment () Int)
(declare-fun c3137c255_total_supply_before_first_deposit () Int)
(assert
 (= c3137c255_assets_to_fulfill_first_deposit c3137c255_assets_to_fulfill_first_deposit))
(assert
 (= c3137c255_first_depositor_share_control c3137c255_first_depositor_share_control))
(assert
 (= c3137c255_shares_received_first_deposit c3137c255_shares_received_first_deposit))
(assert
 (= c3137c255_total_assets_before_first_fulfillment c3137c255_total_assets_before_first_fulfillment))
(assert
 (= c3137c255_total_supply_before_first_deposit c3137c255_total_supply_before_first_deposit))
(define-fun report_preconditions () Bool (and (= 1000000 c3137c255_total_supply_before_first_deposit)
     (= 1 c3137c255_total_assets_before_first_fulfillment)))
(define-fun report_safety () Bool (=> c3137c255_first_depositor_share_control
    (= (* c3137c255_shares_received_first_deposit
          c3137c255_total_assets_before_first_fulfillment)
       (* c3137c255_assets_to_fulfill_first_deposit
          c3137c255_total_supply_before_first_deposit))))
(define-fun report_effects () Bool (and c3137c255_first_depositor_share_control
     c3137c255_first_depositor_share_control))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
