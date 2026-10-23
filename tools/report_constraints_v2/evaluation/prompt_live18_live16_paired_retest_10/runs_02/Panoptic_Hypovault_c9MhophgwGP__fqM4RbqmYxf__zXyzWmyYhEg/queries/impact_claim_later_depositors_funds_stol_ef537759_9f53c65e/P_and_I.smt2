; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca4a8cb03_first_deposit_assets_to_fulfill () Int)
(declare-fun ca4a8cb03_first_deposit_shares_received () Int)
(declare-fun ca4a8cb03_later_depositors_funds_stolen_occurred () Bool)
(declare-fun ca4a8cb03_total_assets_before_first_fulfilment () Int)
(declare-fun ca4a8cb03_total_supply_before_first_fulfilment () Int)
(declare-fun ca4a8cb03_vault_assets_before_first_fulfilment () Int)
(assert
 (= ca4a8cb03_first_deposit_assets_to_fulfill ca4a8cb03_first_deposit_assets_to_fulfill))
(assert
 (= ca4a8cb03_first_deposit_shares_received ca4a8cb03_first_deposit_shares_received))
(assert
 (= ca4a8cb03_later_depositors_funds_stolen_occurred ca4a8cb03_later_depositors_funds_stolen_occurred))
(assert
 (= ca4a8cb03_total_assets_before_first_fulfilment ca4a8cb03_total_assets_before_first_fulfilment))
(assert
 (= ca4a8cb03_total_supply_before_first_fulfilment ca4a8cb03_total_supply_before_first_fulfilment))
(assert
 (= ca4a8cb03_vault_assets_before_first_fulfilment ca4a8cb03_vault_assets_before_first_fulfilment))
(define-fun report_preconditions () Bool (and (= 1000000 ca4a8cb03_total_supply_before_first_fulfilment)
     (= 0 ca4a8cb03_vault_assets_before_first_fulfilment)
     (= 1 ca4a8cb03_total_assets_before_first_fulfilment)))
(define-fun report_safety () Bool (=> ca4a8cb03_later_depositors_funds_stolen_occurred
    (=> (and (= 1000000 ca4a8cb03_total_supply_before_first_fulfilment)
             (= 0 ca4a8cb03_vault_assets_before_first_fulfilment)
             (= 1 ca4a8cb03_total_assets_before_first_fulfilment))
        (= (* ca4a8cb03_first_deposit_shares_received
              ca4a8cb03_total_assets_before_first_fulfilment)
           (* ca4a8cb03_first_deposit_assets_to_fulfill
              ca4a8cb03_total_supply_before_first_fulfilment)))))
(define-fun report_effects () Bool (and ca4a8cb03_later_depositors_funds_stolen_occurred
     (= 1000000 ca4a8cb03_total_supply_before_first_fulfilment)
     (= 0 ca4a8cb03_vault_assets_before_first_fulfilment)
     (= 1 ca4a8cb03_total_assets_before_first_fulfilment)
     (not (= (* ca4a8cb03_first_deposit_shares_received
                ca4a8cb03_total_assets_before_first_fulfilment)
             (* ca4a8cb03_first_deposit_assets_to_fulfill
                ca4a8cb03_total_supply_before_first_fulfilment)))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
