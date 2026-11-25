; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbf177a8e_block_elapsed_since_update () Bool)
(declare-fun cbf177a8e_buyback_at_manipulated_price () Bool)
(declare-fun cbf177a8e_pool_price_skewed () Bool)
(declare-fun cbf177a8e_treasury_funds_available () Bool)
(declare-fun cbf177a8e_twap_equals_single_spot_price () Bool)
(declare-fun cbf177a8e_twap_uses_two_observations () Bool)
(assert
 (= cbf177a8e_block_elapsed_since_update cbf177a8e_block_elapsed_since_update))
(assert
 (= cbf177a8e_buyback_at_manipulated_price cbf177a8e_buyback_at_manipulated_price))
(assert
 (= cbf177a8e_pool_price_skewed cbf177a8e_pool_price_skewed))
(assert
 (= cbf177a8e_treasury_funds_available cbf177a8e_treasury_funds_available))
(assert
 (= cbf177a8e_twap_equals_single_spot_price cbf177a8e_twap_equals_single_spot_price))
(assert
 (= cbf177a8e_twap_uses_two_observations cbf177a8e_twap_uses_two_observations))
(define-fun report_preconditions () Bool (and cbf177a8e_block_elapsed_since_update
     cbf177a8e_pool_price_skewed
     cbf177a8e_treasury_funds_available))
(define-fun report_safety () Bool (=> cbf177a8e_block_elapsed_since_update
    (= cbf177a8e_twap_uses_two_observations
       cbf177a8e_twap_equals_single_spot_price)))
(define-fun report_effects () Bool (and cbf177a8e_block_elapsed_since_update
     (not (= cbf177a8e_twap_uses_two_observations
             cbf177a8e_twap_equals_single_spot_price))
     cbf177a8e_buyback_at_manipulated_price))
