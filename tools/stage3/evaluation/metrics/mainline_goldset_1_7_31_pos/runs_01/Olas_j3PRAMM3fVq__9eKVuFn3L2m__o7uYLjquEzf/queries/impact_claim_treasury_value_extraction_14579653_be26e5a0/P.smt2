; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbbb5f2f7_amount_out_minimum_oracle_based () Bool)
(declare-fun cbbb5f2f7_at_least_one_block_elapsed () Bool)
(declare-fun cbbb5f2f7_funds_available () Bool)
(declare-fun cbbb5f2f7_pool_price_manipulated () Bool)
(declare-fun cbbb5f2f7_swap_executed_at_manipulated_price () Bool)
(assert
 (= cbbb5f2f7_amount_out_minimum_oracle_based cbbb5f2f7_amount_out_minimum_oracle_based))
(assert
 (= cbbb5f2f7_at_least_one_block_elapsed cbbb5f2f7_at_least_one_block_elapsed))
(assert
 (= cbbb5f2f7_funds_available cbbb5f2f7_funds_available))
(assert
 (= cbbb5f2f7_pool_price_manipulated cbbb5f2f7_pool_price_manipulated))
(assert
 (= cbbb5f2f7_swap_executed_at_manipulated_price cbbb5f2f7_swap_executed_at_manipulated_price))
(define-fun report_preconditions () Bool (and cbbb5f2f7_at_least_one_block_elapsed
     cbbb5f2f7_pool_price_manipulated
     cbbb5f2f7_funds_available))
(define-fun report_safety () Bool (=> cbbb5f2f7_pool_price_manipulated cbbb5f2f7_amount_out_minimum_oracle_based))
(define-fun report_effects () Bool (and cbbb5f2f7_pool_price_manipulated
     (not cbbb5f2f7_amount_out_minimum_oracle_based)
     cbbb5f2f7_swap_executed_at_manipulated_price
     (not cbbb5f2f7_amount_out_minimum_oracle_based)))
(assert report_preconditions)
(check-sat)
(get-model)
