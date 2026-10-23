; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c46ac620d_subsequent_deposits_drained_possible () Bool)
(declare-fun c46ac620d_total_assets_before_first_fulfillment () Int)
(declare-fun c46ac620d_total_supply_at_construction () Int)
(declare-fun c46ac620d_underlying_assets_at_construction () Int)
(declare-fun c46ac620d_zero_supply_expected () Int)
(assert
 (= c46ac620d_subsequent_deposits_drained_possible c46ac620d_subsequent_deposits_drained_possible))
(assert
 (= c46ac620d_total_assets_before_first_fulfillment c46ac620d_total_assets_before_first_fulfillment))
(assert
 (= c46ac620d_total_supply_at_construction c46ac620d_total_supply_at_construction))
(assert
 (= c46ac620d_underlying_assets_at_construction c46ac620d_underlying_assets_at_construction))
(assert
 (= c46ac620d_zero_supply_expected c46ac620d_zero_supply_expected))
(define-fun report_preconditions () Bool (and (= 1000000 c46ac620d_total_supply_at_construction)
     (= 0 c46ac620d_underlying_assets_at_construction)
     (= 1 c46ac620d_total_assets_before_first_fulfillment)))
(define-fun report_safety () Bool (=> (= 0 c46ac620d_underlying_assets_at_construction)
    (= c46ac620d_total_supply_at_construction c46ac620d_zero_supply_expected)))
(define-fun report_effects () Bool (and c46ac620d_subsequent_deposits_drained_possible
     c46ac620d_subsequent_deposits_drained_possible))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
