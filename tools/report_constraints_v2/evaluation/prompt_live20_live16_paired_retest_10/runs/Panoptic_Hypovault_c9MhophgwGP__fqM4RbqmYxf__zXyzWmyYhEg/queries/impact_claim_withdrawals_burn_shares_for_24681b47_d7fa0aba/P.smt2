; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cea870213_total_assets_before_first_fulfillment () Int)
(declare-fun cea870213_total_supply_after_constructor () Int)
(declare-fun cea870213_withdrawal_burns_shares_for_tiny_assets () Bool)
(declare-fun cea870213_zero_supply () Int)
(assert
 (= cea870213_total_assets_before_first_fulfillment cea870213_total_assets_before_first_fulfillment))
(assert
 (= cea870213_total_supply_after_constructor cea870213_total_supply_after_constructor))
(assert
 (= cea870213_withdrawal_burns_shares_for_tiny_assets cea870213_withdrawal_burns_shares_for_tiny_assets))
(assert
 (= cea870213_zero_supply cea870213_zero_supply))
(define-fun report_preconditions () Bool (and (= 1000000 cea870213_total_supply_after_constructor)
     (= 1 cea870213_total_assets_before_first_fulfillment)))
(define-fun report_safety () Bool (=> (= 1 cea870213_total_assets_before_first_fulfillment)
    (= cea870213_total_supply_after_constructor cea870213_zero_supply)))
(define-fun report_effects () Bool cea870213_withdrawal_burns_shares_for_tiny_assets)
(assert report_preconditions)
(check-sat)
(get-model)
