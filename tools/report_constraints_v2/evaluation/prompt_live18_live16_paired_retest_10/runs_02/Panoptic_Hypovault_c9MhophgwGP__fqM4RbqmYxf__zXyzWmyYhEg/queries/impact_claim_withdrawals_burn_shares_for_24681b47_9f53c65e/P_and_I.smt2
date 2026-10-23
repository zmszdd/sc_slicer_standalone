; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c52f149cd_first_deposit_assets_to_fulfill () Int)
(declare-fun c52f149cd_first_deposit_shares_received () Int)
(declare-fun c52f149cd_total_assets_before_first_fulfilment () Int)
(declare-fun c52f149cd_total_supply_before_first_fulfilment () Int)
(declare-fun c52f149cd_vault_assets_before_first_fulfilment () Int)
(declare-fun c52f149cd_withdrawal_assets_received () Int)
(declare-fun c52f149cd_withdrawal_shares_burned () Int)
(assert
 (= c52f149cd_first_deposit_assets_to_fulfill c52f149cd_first_deposit_assets_to_fulfill))
(assert
 (= c52f149cd_first_deposit_shares_received c52f149cd_first_deposit_shares_received))
(assert
 (= c52f149cd_total_assets_before_first_fulfilment c52f149cd_total_assets_before_first_fulfilment))
(assert
 (= c52f149cd_total_supply_before_first_fulfilment c52f149cd_total_supply_before_first_fulfilment))
(assert
 (= c52f149cd_vault_assets_before_first_fulfilment c52f149cd_vault_assets_before_first_fulfilment))
(assert
 (= c52f149cd_withdrawal_assets_received c52f149cd_withdrawal_assets_received))
(assert
 (= c52f149cd_withdrawal_shares_burned c52f149cd_withdrawal_shares_burned))
(define-fun report_preconditions () Bool (and (= 1000000 c52f149cd_total_supply_before_first_fulfilment)
     (= 0 c52f149cd_vault_assets_before_first_fulfilment)
     (= 1 c52f149cd_total_assets_before_first_fulfilment)))
(define-fun report_safety () Bool (=> (and (>= 1 c52f149cd_withdrawal_assets_received)
         (< 0 c52f149cd_withdrawal_shares_burned))
    (=> (and (= 1000000 c52f149cd_total_supply_before_first_fulfilment)
             (= 0 c52f149cd_vault_assets_before_first_fulfilment)
             (= 1 c52f149cd_total_assets_before_first_fulfilment))
        (= (* c52f149cd_first_deposit_shares_received
              c52f149cd_total_assets_before_first_fulfilment)
           (* c52f149cd_first_deposit_assets_to_fulfill
              c52f149cd_total_supply_before_first_fulfilment)))))
(define-fun report_effects () Bool (and (>= 1 c52f149cd_withdrawal_assets_received)
     (< 0 c52f149cd_withdrawal_shares_burned)
     (= 1000000 c52f149cd_total_supply_before_first_fulfilment)
     (= 0 c52f149cd_vault_assets_before_first_fulfilment)
     (= 1 c52f149cd_total_assets_before_first_fulfilment)
     (not (= (* c52f149cd_first_deposit_shares_received
                c52f149cd_total_assets_before_first_fulfilment)
             (* c52f149cd_first_deposit_assets_to_fulfill
                c52f149cd_total_supply_before_first_fulfilment)))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
