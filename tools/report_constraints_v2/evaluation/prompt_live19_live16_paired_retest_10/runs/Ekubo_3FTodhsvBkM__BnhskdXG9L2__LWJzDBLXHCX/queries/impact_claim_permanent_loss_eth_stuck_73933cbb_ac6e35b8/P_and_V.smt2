; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c457ca71c_eth_accounted_in_pair_debt () Bool)
(declare-fun c457ca71c_eth_stuck_in_core_forever () Bool)
(declare-fun c457ca71c_msg_value_wei () Int)
(declare-fun c457ca71c_pool_has_liquidity_at_tick_zero () Bool)
(declare-fun c457ca71c_sqrt_ratio_limit_set () Bool)
(assert
 (= c457ca71c_eth_accounted_in_pair_debt c457ca71c_eth_accounted_in_pair_debt))
(assert
 (= c457ca71c_eth_stuck_in_core_forever c457ca71c_eth_stuck_in_core_forever))
(assert
 (= c457ca71c_msg_value_wei c457ca71c_msg_value_wei))
(assert
 (= c457ca71c_pool_has_liquidity_at_tick_zero c457ca71c_pool_has_liquidity_at_tick_zero))
(assert
 (= c457ca71c_sqrt_ratio_limit_set c457ca71c_sqrt_ratio_limit_set))
(define-fun report_preconditions () Bool (and c457ca71c_sqrt_ratio_limit_set
     (< 0 c457ca71c_msg_value_wei)
     c457ca71c_pool_has_liquidity_at_tick_zero))
(define-fun report_safety () Bool (=> c457ca71c_eth_stuck_in_core_forever
    (=> (< 0 c457ca71c_msg_value_wei)
        (= c457ca71c_eth_accounted_in_pair_debt
           c457ca71c_eth_accounted_in_pair_debt))))
(define-fun report_effects () Bool (and c457ca71c_eth_stuck_in_core_forever
     (< 0 c457ca71c_msg_value_wei)
     (not (= c457ca71c_eth_accounted_in_pair_debt
             c457ca71c_eth_accounted_in_pair_debt))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
