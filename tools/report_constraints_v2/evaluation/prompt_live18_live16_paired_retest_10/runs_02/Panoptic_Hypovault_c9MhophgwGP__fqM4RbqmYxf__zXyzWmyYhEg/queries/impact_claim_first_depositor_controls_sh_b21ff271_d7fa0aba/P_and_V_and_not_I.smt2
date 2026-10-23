; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c93954677_first_deposit_cost () Int)
(declare-fun c93954677_first_depositor_shares_after () Int)
(declare-fun c93954677_total_assets_before_first_fulfilment () Int)
(declare-fun c93954677_total_supply_after_first_fulfilment () Int)
(declare-fun c93954677_total_supply_initial () Int)
(declare-fun c93954677_vault_assets_initial () Int)
(assert
 (= c93954677_first_deposit_cost c93954677_first_deposit_cost))
(assert
 (= c93954677_first_depositor_shares_after c93954677_first_depositor_shares_after))
(assert
 (= c93954677_total_assets_before_first_fulfilment c93954677_total_assets_before_first_fulfilment))
(assert
 (= c93954677_total_supply_after_first_fulfilment c93954677_total_supply_after_first_fulfilment))
(assert
 (= c93954677_total_supply_initial c93954677_total_supply_initial))
(assert
 (= c93954677_vault_assets_initial c93954677_vault_assets_initial))
(define-fun report_preconditions () Bool (and (= 1000000 c93954677_total_supply_initial)
     (= 0 c93954677_vault_assets_initial)
     (= 1 c93954677_total_assets_before_first_fulfilment)))
(define-fun report_safety () Bool (=> (>= (* c93954677_first_depositor_shares_after 100)
        (* c93954677_total_supply_after_first_fulfilment 100))
    (=> (and (= 1000000 c93954677_total_supply_initial)
             (= 0 c93954677_vault_assets_initial)
             (= 1 c93954677_total_assets_before_first_fulfilment))
        (<= (* c93954677_first_depositor_shares_after
               c93954677_total_assets_before_first_fulfilment)
            (* c93954677_first_deposit_cost
               c93954677_total_supply_after_first_fulfilment)))))
(define-fun report_effects () Bool (and (>= (* c93954677_first_depositor_shares_after 100)
         (* c93954677_total_supply_after_first_fulfilment 100))
     (= 1000000 c93954677_total_supply_initial)
     (= 0 c93954677_vault_assets_initial)
     (= 1 c93954677_total_assets_before_first_fulfilment)
     (not (<= (* c93954677_first_depositor_shares_after
                 c93954677_total_assets_before_first_fulfilment)
              (* c93954677_first_deposit_cost
                 c93954677_total_supply_after_first_fulfilment)))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
