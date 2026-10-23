; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca2e86812_eth_stuck_forever () Bool)
(declare-fun ca2e86812_pool_initialized_at_tick_zero () Bool)
(declare-fun ca2e86812_swap_is_noop_with_value () Bool)
(declare-fun ca2e86812_victim_sqrt_ratio_limit_set_near_price () Bool)
(declare-fun ca2e86812_victim_swap_msg_value_eth () Int)
(assert
 (= ca2e86812_eth_stuck_forever ca2e86812_eth_stuck_forever))
(assert
 (= ca2e86812_pool_initialized_at_tick_zero ca2e86812_pool_initialized_at_tick_zero))
(assert
 (= ca2e86812_swap_is_noop_with_value ca2e86812_swap_is_noop_with_value))
(assert
 (= ca2e86812_victim_sqrt_ratio_limit_set_near_price ca2e86812_victim_sqrt_ratio_limit_set_near_price))
(assert
 (= ca2e86812_victim_swap_msg_value_eth ca2e86812_victim_swap_msg_value_eth))
(define-fun report_preconditions () Bool (and ca2e86812_pool_initialized_at_tick_zero
     (= 10 ca2e86812_victim_swap_msg_value_eth)
     ca2e86812_victim_sqrt_ratio_limit_set_near_price))
(define-fun report_safety () Bool (=> ca2e86812_eth_stuck_forever
    (=> (and ca2e86812_pool_initialized_at_tick_zero
             (< 0 ca2e86812_victim_swap_msg_value_eth)
             ca2e86812_victim_sqrt_ratio_limit_set_near_price)
        (not ca2e86812_swap_is_noop_with_value))))
(define-fun report_effects () Bool (and ca2e86812_eth_stuck_forever
     ca2e86812_pool_initialized_at_tick_zero
     (< 0 ca2e86812_victim_swap_msg_value_eth)
     ca2e86812_victim_sqrt_ratio_limit_set_near_price
     (not (not ca2e86812_swap_is_noop_with_value))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
