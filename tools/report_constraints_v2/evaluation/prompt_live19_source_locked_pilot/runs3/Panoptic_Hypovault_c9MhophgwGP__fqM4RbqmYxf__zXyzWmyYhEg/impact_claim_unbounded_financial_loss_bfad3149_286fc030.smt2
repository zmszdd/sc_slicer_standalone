; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cf0a331e7_first_deposit_assets_to_fulfill () Int)
(declare-fun cf0a331e7_first_deposit_shares_received () Int)
(declare-fun cf0a331e7_subsequent_deposits_drained () Bool)
(declare-fun cf0a331e7_total_assets_before_first_fulfillment () Int)
(declare-fun cf0a331e7_total_supply_before_first_fulfillment () Int)
(declare-fun cf0a331e7_vault_underlying_assets_before_first_fulfillment () Int)
(assert
 (= cf0a331e7_first_deposit_assets_to_fulfill cf0a331e7_first_deposit_assets_to_fulfill))
(assert
 (= cf0a331e7_first_deposit_shares_received cf0a331e7_first_deposit_shares_received))
(assert
 (= cf0a331e7_subsequent_deposits_drained cf0a331e7_subsequent_deposits_drained))
(assert
 (= cf0a331e7_total_assets_before_first_fulfillment cf0a331e7_total_assets_before_first_fulfillment))
(assert
 (= cf0a331e7_total_supply_before_first_fulfillment cf0a331e7_total_supply_before_first_fulfillment))
(assert
 (= cf0a331e7_vault_underlying_assets_before_first_fulfillment cf0a331e7_vault_underlying_assets_before_first_fulfillment))
(define-fun report_preconditions () Bool (and (= 1000000 cf0a331e7_total_supply_before_first_fulfillment)
     (= 0 cf0a331e7_vault_underlying_assets_before_first_fulfillment)
     (= 1 cf0a331e7_total_assets_before_first_fulfillment)))
(define-fun report_safety () Bool (=> (= 1 cf0a331e7_total_assets_before_first_fulfillment)
    (= (* cf0a331e7_first_deposit_shares_received
          cf0a331e7_total_assets_before_first_fulfillment)
       (* cf0a331e7_first_deposit_assets_to_fulfill
          cf0a331e7_total_supply_before_first_fulfillment))))
(define-fun report_effects () Bool (and cf0a331e7_subsequent_deposits_drained
     cf0a331e7_subsequent_deposits_drained))
