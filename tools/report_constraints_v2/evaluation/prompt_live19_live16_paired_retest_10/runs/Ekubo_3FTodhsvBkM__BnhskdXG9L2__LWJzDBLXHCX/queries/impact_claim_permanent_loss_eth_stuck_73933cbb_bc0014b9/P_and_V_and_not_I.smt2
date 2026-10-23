; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c693e6982_eth_recoverable_via_withdraw () Bool)
(declare-fun c693e6982_eth_stuck_forever () Bool)
(declare-fun c693e6982_msg_value_eth () Int)
(declare-fun c693e6982_pool_initialized_with_liquidity () Bool)
(declare-fun c693e6982_sqrt_ratio_limit_set_near_price () Bool)
(assert
 (= c693e6982_eth_recoverable_via_withdraw c693e6982_eth_recoverable_via_withdraw))
(assert
 (= c693e6982_eth_stuck_forever c693e6982_eth_stuck_forever))
(assert
 (= c693e6982_msg_value_eth c693e6982_msg_value_eth))
(assert
 (= c693e6982_pool_initialized_with_liquidity c693e6982_pool_initialized_with_liquidity))
(assert
 (= c693e6982_sqrt_ratio_limit_set_near_price c693e6982_sqrt_ratio_limit_set_near_price))
(define-fun report_preconditions () Bool (and c693e6982_sqrt_ratio_limit_set_near_price
     (< 0 c693e6982_msg_value_eth)
     c693e6982_pool_initialized_with_liquidity))
(define-fun report_safety () Bool (=> c693e6982_eth_stuck_forever
    (=> (and c693e6982_sqrt_ratio_limit_set_near_price
             (< 0 c693e6982_msg_value_eth)
             c693e6982_pool_initialized_with_liquidity)
        c693e6982_eth_recoverable_via_withdraw)))
(define-fun report_effects () Bool (and c693e6982_eth_stuck_forever
     c693e6982_sqrt_ratio_limit_set_near_price
     (< 0 c693e6982_msg_value_eth)
     c693e6982_pool_initialized_with_liquidity
     (not c693e6982_eth_recoverable_via_withdraw)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
