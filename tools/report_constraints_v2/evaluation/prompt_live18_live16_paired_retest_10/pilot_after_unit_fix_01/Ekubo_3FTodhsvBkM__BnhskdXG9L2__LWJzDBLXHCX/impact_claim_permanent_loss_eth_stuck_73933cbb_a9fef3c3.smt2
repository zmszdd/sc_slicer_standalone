; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc667e2e4_attacker_moved_price_to_limit () Bool)
(declare-fun cc667e2e4_eth_stuck_forever () Bool)
(declare-fun cc667e2e4_pool_initialized_at_tick_zero () Bool)
(declare-fun cc667e2e4_swap_is_noop_with_value () Bool)
(declare-fun cc667e2e4_victim_msg_value_eth () Int)
(declare-fun cc667e2e4_victim_sqrt_ratio_limit_set_near_price () Bool)
(assert
 (= cc667e2e4_attacker_moved_price_to_limit cc667e2e4_attacker_moved_price_to_limit))
(assert
 (= cc667e2e4_eth_stuck_forever cc667e2e4_eth_stuck_forever))
(assert
 (= cc667e2e4_pool_initialized_at_tick_zero cc667e2e4_pool_initialized_at_tick_zero))
(assert
 (= cc667e2e4_swap_is_noop_with_value cc667e2e4_swap_is_noop_with_value))
(assert
 (= cc667e2e4_victim_msg_value_eth cc667e2e4_victim_msg_value_eth))
(assert
 (= cc667e2e4_victim_sqrt_ratio_limit_set_near_price cc667e2e4_victim_sqrt_ratio_limit_set_near_price))
(define-fun report_preconditions () Bool (and cc667e2e4_pool_initialized_at_tick_zero
     cc667e2e4_victim_sqrt_ratio_limit_set_near_price
     (= 10 cc667e2e4_victim_msg_value_eth)
     cc667e2e4_attacker_moved_price_to_limit))
(define-fun report_safety () Bool (=> cc667e2e4_eth_stuck_forever
    (=> cc667e2e4_swap_is_noop_with_value (not cc667e2e4_eth_stuck_forever))))
(define-fun report_effects () Bool (and cc667e2e4_eth_stuck_forever
     cc667e2e4_swap_is_noop_with_value
     (not (not cc667e2e4_eth_stuck_forever))))
