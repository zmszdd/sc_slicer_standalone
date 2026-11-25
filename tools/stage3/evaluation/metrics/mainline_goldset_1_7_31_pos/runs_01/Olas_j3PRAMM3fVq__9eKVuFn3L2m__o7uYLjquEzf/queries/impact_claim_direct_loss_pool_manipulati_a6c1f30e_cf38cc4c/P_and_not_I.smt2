; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c291bb573_block_elapsed_since_update () Bool)
(declare-fun c291bb573_buyback_executed_at_manipulated_price () Bool)
(declare-fun c291bb573_oracle_uses_single_spot_price () Bool)
(declare-fun c291bb573_oracle_uses_two_observations () Bool)
(declare-fun c291bb573_pool_price_manipulated () Bool)
(declare-fun c291bb573_treasury_funds_available () Bool)
(assert
 (= c291bb573_block_elapsed_since_update c291bb573_block_elapsed_since_update))
(assert
 (= c291bb573_buyback_executed_at_manipulated_price c291bb573_buyback_executed_at_manipulated_price))
(assert
 (= c291bb573_oracle_uses_single_spot_price c291bb573_oracle_uses_single_spot_price))
(assert
 (= c291bb573_oracle_uses_two_observations c291bb573_oracle_uses_two_observations))
(assert
 (= c291bb573_pool_price_manipulated c291bb573_pool_price_manipulated))
(assert
 (= c291bb573_treasury_funds_available c291bb573_treasury_funds_available))
(define-fun report_preconditions () Bool (and c291bb573_block_elapsed_since_update
     c291bb573_pool_price_manipulated
     c291bb573_treasury_funds_available
     c291bb573_oracle_uses_single_spot_price))
(define-fun report_safety () Bool (= c291bb573_oracle_uses_single_spot_price
   c291bb573_oracle_uses_two_observations))
(define-fun report_effects () Bool (and c291bb573_oracle_uses_single_spot_price
     (not (= c291bb573_oracle_uses_single_spot_price
             c291bb573_oracle_uses_two_observations))
     c291bb573_buyback_executed_at_manipulated_price
     c291bb573_pool_price_manipulated))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
