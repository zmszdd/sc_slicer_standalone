; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8d0ecac3_blocks_elapsed_since_update () Int)
(declare-fun c8d0ecac3_buyback_executed_at_manipulated_price () Bool)
(declare-fun c8d0ecac3_pool_price_skewed () Bool)
(declare-fun c8d0ecac3_slippage_check_fails_on_extreme_deviation () Bool)
(declare-fun c8d0ecac3_treasury_funds_available () Bool)
(declare-fun c8d0ecac3_treasury_value_extracted () Bool)
(declare-fun c8d0ecac3_twap_equals_spot_price () Bool)
(assert
 (= c8d0ecac3_blocks_elapsed_since_update c8d0ecac3_blocks_elapsed_since_update))
(assert
 (= c8d0ecac3_buyback_executed_at_manipulated_price c8d0ecac3_buyback_executed_at_manipulated_price))
(assert
 (= c8d0ecac3_pool_price_skewed c8d0ecac3_pool_price_skewed))
(assert
 (= c8d0ecac3_slippage_check_fails_on_extreme_deviation c8d0ecac3_slippage_check_fails_on_extreme_deviation))
(assert
 (= c8d0ecac3_treasury_funds_available c8d0ecac3_treasury_funds_available))
(assert
 (= c8d0ecac3_treasury_value_extracted c8d0ecac3_treasury_value_extracted))
(assert
 (= c8d0ecac3_twap_equals_spot_price c8d0ecac3_twap_equals_spot_price))
(define-fun report_preconditions () Bool (and (<= 1 c8d0ecac3_blocks_elapsed_since_update)
     c8d0ecac3_pool_price_skewed
     c8d0ecac3_treasury_funds_available
     (not c8d0ecac3_twap_equals_spot_price)))
(define-fun report_safety () Bool c8d0ecac3_slippage_check_fails_on_extreme_deviation)
(define-fun report_effects () Bool (and (not c8d0ecac3_twap_equals_spot_price)
     (not c8d0ecac3_slippage_check_fails_on_extreme_deviation)
     c8d0ecac3_buyback_executed_at_manipulated_price
     c8d0ecac3_treasury_value_extracted))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
