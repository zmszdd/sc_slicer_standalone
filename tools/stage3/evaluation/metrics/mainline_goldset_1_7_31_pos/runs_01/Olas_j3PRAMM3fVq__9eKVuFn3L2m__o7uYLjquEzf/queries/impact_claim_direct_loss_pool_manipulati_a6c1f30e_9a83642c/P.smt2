; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca557870c_block_elapsed_since_update () Bool)
(declare-fun ca557870c_buyback_executed () Bool)
(declare-fun ca557870c_direct_loss_occurred () Bool)
(declare-fun ca557870c_pool_price_skewed () Bool)
(declare-fun ca557870c_treasury_funds_available () Bool)
(declare-fun ca557870c_twap_guard_effective () Bool)
(assert
 (= ca557870c_block_elapsed_since_update ca557870c_block_elapsed_since_update))
(assert
 (= ca557870c_buyback_executed ca557870c_buyback_executed))
(assert
 (= ca557870c_direct_loss_occurred ca557870c_direct_loss_occurred))
(assert
 (= ca557870c_pool_price_skewed ca557870c_pool_price_skewed))
(assert
 (= ca557870c_treasury_funds_available ca557870c_treasury_funds_available))
(assert
 (= ca557870c_twap_guard_effective ca557870c_twap_guard_effective))
(define-fun report_preconditions () Bool (and ca557870c_block_elapsed_since_update
     ca557870c_pool_price_skewed
     ca557870c_treasury_funds_available))
(define-fun report_safety () Bool (=> ca557870c_buyback_executed ca557870c_twap_guard_effective))
(define-fun report_effects () Bool (and ca557870c_buyback_executed
     (not ca557870c_twap_guard_effective)
     ca557870c_direct_loss_occurred
     ca557870c_pool_price_skewed))
(assert report_preconditions)
(check-sat)
(get-model)
