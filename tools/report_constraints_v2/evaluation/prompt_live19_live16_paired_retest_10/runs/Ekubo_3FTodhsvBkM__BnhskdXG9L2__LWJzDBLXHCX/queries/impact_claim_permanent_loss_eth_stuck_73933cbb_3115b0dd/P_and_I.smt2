; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7a49acce_eth_stuck_forever () Bool)
(declare-fun c7a49acce_msg_value_nonzero () Bool)
(declare-fun c7a49acce_noop_swap_with_value () Bool)
(declare-fun c7a49acce_pool_initialized_with_liquidity () Bool)
(declare-fun c7a49acce_sqrt_ratio_limit_set_near_price () Bool)
(declare-fun c7a49acce_swap_reverted () Bool)
(assert
 (= c7a49acce_eth_stuck_forever c7a49acce_eth_stuck_forever))
(assert
 (= c7a49acce_msg_value_nonzero c7a49acce_msg_value_nonzero))
(assert
 (= c7a49acce_noop_swap_with_value c7a49acce_noop_swap_with_value))
(assert
 (= c7a49acce_pool_initialized_with_liquidity c7a49acce_pool_initialized_with_liquidity))
(assert
 (= c7a49acce_sqrt_ratio_limit_set_near_price c7a49acce_sqrt_ratio_limit_set_near_price))
(assert
 (= c7a49acce_swap_reverted c7a49acce_swap_reverted))
(define-fun report_preconditions () Bool (and c7a49acce_sqrt_ratio_limit_set_near_price
     c7a49acce_msg_value_nonzero
     c7a49acce_pool_initialized_with_liquidity))
(define-fun report_safety () Bool (=> c7a49acce_eth_stuck_forever
    (=> c7a49acce_noop_swap_with_value c7a49acce_swap_reverted)))
(define-fun report_effects () Bool (and c7a49acce_eth_stuck_forever
     c7a49acce_noop_swap_with_value
     (not c7a49acce_swap_reverted)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
