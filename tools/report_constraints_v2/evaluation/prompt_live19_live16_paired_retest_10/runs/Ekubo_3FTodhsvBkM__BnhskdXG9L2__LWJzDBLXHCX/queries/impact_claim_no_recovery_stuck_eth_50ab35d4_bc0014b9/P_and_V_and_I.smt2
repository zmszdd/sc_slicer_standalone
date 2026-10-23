; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc4c8310c_eth_recoverable_via_withdraw () Bool)
(declare-fun cc4c8310c_msg_value_ether () Int)
(declare-fun cc4c8310c_pool_initialized_with_liquidity () Bool)
(declare-fun cc4c8310c_sqrt_ratio_limit_set_near_price () Bool)
(declare-fun cc4c8310c_stuck_eth_extractable () Bool)
(assert
 (= cc4c8310c_eth_recoverable_via_withdraw cc4c8310c_eth_recoverable_via_withdraw))
(assert
 (= cc4c8310c_msg_value_ether cc4c8310c_msg_value_ether))
(assert
 (= cc4c8310c_pool_initialized_with_liquidity cc4c8310c_pool_initialized_with_liquidity))
(assert
 (= cc4c8310c_sqrt_ratio_limit_set_near_price cc4c8310c_sqrt_ratio_limit_set_near_price))
(assert
 (= cc4c8310c_stuck_eth_extractable cc4c8310c_stuck_eth_extractable))
(define-fun report_preconditions () Bool (and cc4c8310c_sqrt_ratio_limit_set_near_price
     (< 0 cc4c8310c_msg_value_ether)
     cc4c8310c_pool_initialized_with_liquidity))
(define-fun report_safety () Bool (=> (not cc4c8310c_stuck_eth_extractable)
    (=> (and cc4c8310c_sqrt_ratio_limit_set_near_price
             (< 0 cc4c8310c_msg_value_ether)
             cc4c8310c_pool_initialized_with_liquidity)
        cc4c8310c_eth_recoverable_via_withdraw)))
(define-fun report_effects () Bool (and (not cc4c8310c_stuck_eth_extractable)
     cc4c8310c_sqrt_ratio_limit_set_near_price
     (< 0 cc4c8310c_msg_value_ether)
     cc4c8310c_pool_initialized_with_liquidity
     (not cc4c8310c_eth_recoverable_via_withdraw)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
