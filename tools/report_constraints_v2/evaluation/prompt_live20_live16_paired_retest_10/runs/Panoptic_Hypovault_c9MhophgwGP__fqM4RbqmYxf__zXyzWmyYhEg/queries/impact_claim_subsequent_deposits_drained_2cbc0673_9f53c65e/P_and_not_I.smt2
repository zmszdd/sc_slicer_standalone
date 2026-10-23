; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c90721643_first_deposit_assets_to_fulfill () Int)
(declare-fun c90721643_first_deposit_shares_received () Int)
(declare-fun c90721643_subsequent_deposits_drained_occurred () Bool)
(declare-fun c90721643_total_assets_before_first_fulfillment () Int)
(declare-fun c90721643_total_supply_preset () Int)
(declare-fun c90721643_vault_underlying_assets_at_constructor () Int)
(assert
 (= c90721643_first_deposit_assets_to_fulfill c90721643_first_deposit_assets_to_fulfill))
(assert
 (= c90721643_first_deposit_shares_received c90721643_first_deposit_shares_received))
(assert
 (= c90721643_subsequent_deposits_drained_occurred c90721643_subsequent_deposits_drained_occurred))
(assert
 (= c90721643_total_assets_before_first_fulfillment c90721643_total_assets_before_first_fulfillment))
(assert
 (= c90721643_total_supply_preset c90721643_total_supply_preset))
(assert
 (= c90721643_vault_underlying_assets_at_constructor c90721643_vault_underlying_assets_at_constructor))
(define-fun report_preconditions () Bool (and (= 1000000 c90721643_total_supply_preset)
     (= 0 c90721643_vault_underlying_assets_at_constructor)
     (= 1 c90721643_total_assets_before_first_fulfillment)))
(define-fun report_safety () Bool (=> (= 1 c90721643_total_assets_before_first_fulfillment)
    (= (* c90721643_first_deposit_shares_received
          c90721643_total_assets_before_first_fulfillment)
       (* c90721643_first_deposit_assets_to_fulfill
          c90721643_total_supply_preset))))
(define-fun report_effects () Bool (and c90721643_subsequent_deposits_drained_occurred
     c90721643_subsequent_deposits_drained_occurred))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
