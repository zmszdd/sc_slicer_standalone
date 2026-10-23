; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c693e6982_eth_stuck_forever () Bool)
(declare-fun c693e6982_pool_initialized_at_tick_zero () Bool)
(declare-fun c693e6982_victim_swap_msg_value_nonzero () Bool)
(declare-fun c693e6982_victim_swap_sqrt_ratio_limit_near_price () Bool)
(assert
 (= c693e6982_eth_stuck_forever c693e6982_eth_stuck_forever))
(assert
 (= c693e6982_pool_initialized_at_tick_zero c693e6982_pool_initialized_at_tick_zero))
(assert
 (= c693e6982_victim_swap_msg_value_nonzero c693e6982_victim_swap_msg_value_nonzero))
(assert
 (= c693e6982_victim_swap_sqrt_ratio_limit_near_price c693e6982_victim_swap_sqrt_ratio_limit_near_price))
(define-fun report_preconditions () Bool (and c693e6982_pool_initialized_at_tick_zero
     c693e6982_victim_swap_sqrt_ratio_limit_near_price
     c693e6982_victim_swap_msg_value_nonzero))
(define-fun report_safety () Bool (=> c693e6982_eth_stuck_forever
    (=> (and c693e6982_pool_initialized_at_tick_zero
             c693e6982_victim_swap_sqrt_ratio_limit_near_price
             c693e6982_victim_swap_msg_value_nonzero)
        (not c693e6982_eth_stuck_forever))))
(define-fun report_effects () Bool (and c693e6982_eth_stuck_forever
     c693e6982_pool_initialized_at_tick_zero
     c693e6982_victim_swap_sqrt_ratio_limit_near_price
     c693e6982_victim_swap_msg_value_nonzero
     (not (not c693e6982_eth_stuck_forever))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
