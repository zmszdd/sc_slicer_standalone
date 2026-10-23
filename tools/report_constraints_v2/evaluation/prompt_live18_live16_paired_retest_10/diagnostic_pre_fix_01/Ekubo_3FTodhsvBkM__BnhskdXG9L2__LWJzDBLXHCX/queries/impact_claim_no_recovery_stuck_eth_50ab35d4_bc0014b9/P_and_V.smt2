; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc4c8310c_eth_recoverable_after_swap () Bool)
(declare-fun cc4c8310c_pool_initialized_at_tick_zero () Bool)
(declare-fun cc4c8310c_stuck_eth_not_extractable () Bool)
(declare-fun cc4c8310c_victim_swap_eth_value_nonzero () Bool)
(declare-fun cc4c8310c_victim_swap_has_sqrt_ratio_limit_near_price () Bool)
(assert
 (= cc4c8310c_eth_recoverable_after_swap cc4c8310c_eth_recoverable_after_swap))
(assert
 (= cc4c8310c_pool_initialized_at_tick_zero cc4c8310c_pool_initialized_at_tick_zero))
(assert
 (= cc4c8310c_stuck_eth_not_extractable cc4c8310c_stuck_eth_not_extractable))
(assert
 (= cc4c8310c_victim_swap_eth_value_nonzero cc4c8310c_victim_swap_eth_value_nonzero))
(assert
 (= cc4c8310c_victim_swap_has_sqrt_ratio_limit_near_price cc4c8310c_victim_swap_has_sqrt_ratio_limit_near_price))
(define-fun report_preconditions () Bool (and cc4c8310c_pool_initialized_at_tick_zero
     cc4c8310c_victim_swap_has_sqrt_ratio_limit_near_price
     cc4c8310c_victim_swap_eth_value_nonzero))
(define-fun report_safety () Bool (=> cc4c8310c_stuck_eth_not_extractable
    (=> (and cc4c8310c_pool_initialized_at_tick_zero
             cc4c8310c_victim_swap_has_sqrt_ratio_limit_near_price
             cc4c8310c_victim_swap_eth_value_nonzero)
        cc4c8310c_eth_recoverable_after_swap)))
(define-fun report_effects () Bool (and cc4c8310c_stuck_eth_not_extractable
     cc4c8310c_pool_initialized_at_tick_zero
     cc4c8310c_victim_swap_has_sqrt_ratio_limit_near_price
     cc4c8310c_victim_swap_eth_value_nonzero
     (not cc4c8310c_eth_recoverable_after_swap)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
