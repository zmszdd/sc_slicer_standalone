; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c5b7affa8_eth_silently_accepted () Bool)
(declare-fun c5b7affa8_pool_initialized_at_tick_zero () Bool)
(declare-fun c5b7affa8_swap_is_noop () Bool)
(declare-fun c5b7affa8_triggered_by_legitimate_swap () Bool)
(declare-fun c5b7affa8_victim_sqrt_ratio_limit_near_price () Bool)
(declare-fun c5b7affa8_victim_swap_msg_value_wei () Int)
(assert
 (= c5b7affa8_eth_silently_accepted c5b7affa8_eth_silently_accepted))
(assert
 (= c5b7affa8_pool_initialized_at_tick_zero c5b7affa8_pool_initialized_at_tick_zero))
(assert
 (= c5b7affa8_swap_is_noop c5b7affa8_swap_is_noop))
(assert
 (= c5b7affa8_triggered_by_legitimate_swap c5b7affa8_triggered_by_legitimate_swap))
(assert
 (= c5b7affa8_victim_sqrt_ratio_limit_near_price c5b7affa8_victim_sqrt_ratio_limit_near_price))
(assert
 (= c5b7affa8_victim_swap_msg_value_wei c5b7affa8_victim_swap_msg_value_wei))
(define-fun report_preconditions () Bool (and c5b7affa8_pool_initialized_at_tick_zero
     c5b7affa8_victim_sqrt_ratio_limit_near_price
     (< 0 c5b7affa8_victim_swap_msg_value_wei)))
(define-fun report_safety () Bool (=> c5b7affa8_triggered_by_legitimate_swap
    (=> (and c5b7affa8_swap_is_noop (< 0 c5b7affa8_victim_swap_msg_value_wei))
        (not c5b7affa8_eth_silently_accepted))))
(define-fun report_effects () Bool (and c5b7affa8_triggered_by_legitimate_swap
     c5b7affa8_swap_is_noop
     (< 0 c5b7affa8_victim_swap_msg_value_wei)
     (not (not c5b7affa8_eth_silently_accepted))))
