; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cce964735_msg_value_nonzero () Bool)
(declare-fun cce964735_pool_initialized_with_liquidity () Bool)
(declare-fun cce964735_sqrt_ratio_limit_set_near_price () Bool)
(declare-fun cce964735_stuck_eth_extractable () Bool)
(declare-fun cce964735_swap_is_noop_with_value () Bool)
(declare-fun cce964735_swap_reverts () Bool)
(assert
 (= cce964735_msg_value_nonzero cce964735_msg_value_nonzero))
(assert
 (= cce964735_pool_initialized_with_liquidity cce964735_pool_initialized_with_liquidity))
(assert
 (= cce964735_sqrt_ratio_limit_set_near_price cce964735_sqrt_ratio_limit_set_near_price))
(assert
 (= cce964735_stuck_eth_extractable cce964735_stuck_eth_extractable))
(assert
 (= cce964735_swap_is_noop_with_value cce964735_swap_is_noop_with_value))
(assert
 (= cce964735_swap_reverts cce964735_swap_reverts))
(define-fun report_preconditions () Bool (and cce964735_sqrt_ratio_limit_set_near_price
     cce964735_msg_value_nonzero
     cce964735_pool_initialized_with_liquidity))
(define-fun report_safety () Bool (=> (not cce964735_stuck_eth_extractable)
    (=> cce964735_swap_is_noop_with_value cce964735_swap_reverts)))
(define-fun report_effects () Bool (and (not cce964735_stuck_eth_extractable)
     cce964735_swap_is_noop_with_value
     (not cce964735_swap_reverts)))
