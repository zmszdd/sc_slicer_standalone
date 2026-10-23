; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd55ac2fd_subsequent_deposits_drained () Bool)
(declare-fun cd55ac2fd_total_assets_before_first_fulfillment () Int)
(declare-fun cd55ac2fd_total_supply_at_construction () Int)
(declare-fun cd55ac2fd_vault_underlying_assets_at_construction () Int)
(declare-fun cd55ac2fd_zero_assets () Int)
(declare-fun cd55ac2fd_zero_supply () Int)
(assert
 (= cd55ac2fd_subsequent_deposits_drained cd55ac2fd_subsequent_deposits_drained))
(assert
 (= cd55ac2fd_total_assets_before_first_fulfillment cd55ac2fd_total_assets_before_first_fulfillment))
(assert
 (= cd55ac2fd_total_supply_at_construction cd55ac2fd_total_supply_at_construction))
(assert
 (= cd55ac2fd_vault_underlying_assets_at_construction cd55ac2fd_vault_underlying_assets_at_construction))
(assert
 (= cd55ac2fd_zero_assets cd55ac2fd_zero_assets))
(assert
 (= cd55ac2fd_zero_supply cd55ac2fd_zero_supply))
(define-fun report_preconditions () Bool (and (= 1000000 cd55ac2fd_total_supply_at_construction)
     (= 0 cd55ac2fd_vault_underlying_assets_at_construction)
     (= 1 cd55ac2fd_total_assets_before_first_fulfillment)))
(define-fun report_safety () Bool (=> (and (= cd55ac2fd_total_supply_at_construction cd55ac2fd_zero_supply)
         (= cd55ac2fd_vault_underlying_assets_at_construction
            cd55ac2fd_zero_assets))
    (= cd55ac2fd_total_supply_at_construction cd55ac2fd_zero_supply)))
(define-fun report_effects () Bool (and cd55ac2fd_subsequent_deposits_drained
     cd55ac2fd_subsequent_deposits_drained))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
