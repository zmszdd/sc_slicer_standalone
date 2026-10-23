; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8b3ae602_first_deposit_assets_to_fulfill () Int)
(declare-fun c8b3ae602_first_deposit_shares_received () Int)
(declare-fun c8b3ae602_subsequent_deposits_drainable () Bool)
(declare-fun c8b3ae602_total_assets_before_first_fulfilment () Int)
(declare-fun c8b3ae602_total_supply_before_first_fulfilment () Int)
(declare-fun c8b3ae602_vault_assets_before_first_fulfilment () Int)
(assert
 (= c8b3ae602_first_deposit_assets_to_fulfill c8b3ae602_first_deposit_assets_to_fulfill))
(assert
 (= c8b3ae602_first_deposit_shares_received c8b3ae602_first_deposit_shares_received))
(assert
 (= c8b3ae602_subsequent_deposits_drainable c8b3ae602_subsequent_deposits_drainable))
(assert
 (= c8b3ae602_total_assets_before_first_fulfilment c8b3ae602_total_assets_before_first_fulfilment))
(assert
 (= c8b3ae602_total_supply_before_first_fulfilment c8b3ae602_total_supply_before_first_fulfilment))
(assert
 (= c8b3ae602_vault_assets_before_first_fulfilment c8b3ae602_vault_assets_before_first_fulfilment))
(define-fun report_preconditions () Bool (and (= 1000000 c8b3ae602_total_supply_before_first_fulfilment)
     (= 0 c8b3ae602_vault_assets_before_first_fulfilment)
     (= 1 c8b3ae602_total_assets_before_first_fulfilment)))
(define-fun report_safety () Bool (=> c8b3ae602_subsequent_deposits_drainable
    (=> (and (= 1000000 c8b3ae602_total_supply_before_first_fulfilment)
             (= 0 c8b3ae602_vault_assets_before_first_fulfilment)
             (= 1 c8b3ae602_total_assets_before_first_fulfilment))
        (= (* c8b3ae602_first_deposit_shares_received
              c8b3ae602_total_assets_before_first_fulfilment)
           (* c8b3ae602_first_deposit_assets_to_fulfill
              c8b3ae602_total_supply_before_first_fulfilment)))))
(define-fun report_effects () Bool (and c8b3ae602_subsequent_deposits_drainable
     (= 1000000 c8b3ae602_total_supply_before_first_fulfilment)
     (= 0 c8b3ae602_vault_assets_before_first_fulfilment)
     (= 1 c8b3ae602_total_assets_before_first_fulfilment)
     (not (= (* c8b3ae602_first_deposit_shares_received
                c8b3ae602_total_assets_before_first_fulfilment)
             (* c8b3ae602_first_deposit_assets_to_fulfill
                c8b3ae602_total_supply_before_first_fulfilment)))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
