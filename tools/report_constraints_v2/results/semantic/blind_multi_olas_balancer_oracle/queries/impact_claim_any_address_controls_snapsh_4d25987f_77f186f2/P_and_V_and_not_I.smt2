; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb81930f6_any_address_decides_snapshot_update_timing () Bool)
(declare-fun cb81930f6_snapshot_steered_away_from_original_market_price () Bool)
(declare-fun cb81930f6_update_price_callable_by_any_address () Bool)
(assert
 (= cb81930f6_any_address_decides_snapshot_update_timing cb81930f6_any_address_decides_snapshot_update_timing))
(assert
 (= cb81930f6_snapshot_steered_away_from_original_market_price cb81930f6_snapshot_steered_away_from_original_market_price))
(assert
 (= cb81930f6_update_price_callable_by_any_address cb81930f6_update_price_callable_by_any_address))
(define-fun report_preconditions () Bool cb81930f6_update_price_callable_by_any_address)
(define-fun report_safety () Bool (=> cb81930f6_snapshot_steered_away_from_original_market_price
    (not cb81930f6_snapshot_steered_away_from_original_market_price)))
(define-fun report_effects () Bool (and cb81930f6_any_address_decides_snapshot_update_timing
     cb81930f6_any_address_decides_snapshot_update_timing))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
