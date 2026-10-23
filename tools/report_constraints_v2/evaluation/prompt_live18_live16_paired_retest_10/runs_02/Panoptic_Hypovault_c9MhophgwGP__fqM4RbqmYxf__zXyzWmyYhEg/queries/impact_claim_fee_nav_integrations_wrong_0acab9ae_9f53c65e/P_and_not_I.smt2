; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ccbfc8c63_first_deposit_assets_to_fulfill () Int)
(declare-fun ccbfc8c63_first_deposit_shares_received () Int)
(declare-fun ccbfc8c63_share_price_reporting_wrong () Bool)
(declare-fun ccbfc8c63_total_assets_before_first_fulfilment () Int)
(declare-fun ccbfc8c63_total_supply_before_first_fulfilment () Int)
(declare-fun ccbfc8c63_vault_assets_before_first_fulfilment () Int)
(assert
 (= ccbfc8c63_first_deposit_assets_to_fulfill ccbfc8c63_first_deposit_assets_to_fulfill))
(assert
 (= ccbfc8c63_first_deposit_shares_received ccbfc8c63_first_deposit_shares_received))
(assert
 (= ccbfc8c63_share_price_reporting_wrong ccbfc8c63_share_price_reporting_wrong))
(assert
 (= ccbfc8c63_total_assets_before_first_fulfilment ccbfc8c63_total_assets_before_first_fulfilment))
(assert
 (= ccbfc8c63_total_supply_before_first_fulfilment ccbfc8c63_total_supply_before_first_fulfilment))
(assert
 (= ccbfc8c63_vault_assets_before_first_fulfilment ccbfc8c63_vault_assets_before_first_fulfilment))
(define-fun report_preconditions () Bool (and (= 1000000 ccbfc8c63_total_supply_before_first_fulfilment)
     (= 0 ccbfc8c63_vault_assets_before_first_fulfilment)
     (= 1 ccbfc8c63_total_assets_before_first_fulfilment)))
(define-fun report_safety () Bool (=> ccbfc8c63_share_price_reporting_wrong
    (=> (and (= 1000000 ccbfc8c63_total_supply_before_first_fulfilment)
             (= 0 ccbfc8c63_vault_assets_before_first_fulfilment)
             (= 1 ccbfc8c63_total_assets_before_first_fulfilment))
        (= (* ccbfc8c63_first_deposit_shares_received
              ccbfc8c63_total_assets_before_first_fulfilment)
           (* ccbfc8c63_first_deposit_assets_to_fulfill
              ccbfc8c63_total_supply_before_first_fulfilment)))))
(define-fun report_effects () Bool (and ccbfc8c63_share_price_reporting_wrong
     (= 1000000 ccbfc8c63_total_supply_before_first_fulfilment)
     (= 0 ccbfc8c63_vault_assets_before_first_fulfilment)
     (= 1 ccbfc8c63_total_assets_before_first_fulfilment)
     (not (= (* ccbfc8c63_first_deposit_shares_received
                ccbfc8c63_total_assets_before_first_fulfilment)
             (* ccbfc8c63_first_deposit_assets_to_fulfill
                ccbfc8c63_total_supply_before_first_fulfilment)))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
