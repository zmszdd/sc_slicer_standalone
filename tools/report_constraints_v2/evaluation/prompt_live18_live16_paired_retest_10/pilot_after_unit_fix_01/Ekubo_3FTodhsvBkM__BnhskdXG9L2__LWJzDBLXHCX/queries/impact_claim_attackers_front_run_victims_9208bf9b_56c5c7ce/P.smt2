; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2b40e0c6_attacker_moved_price_to_victim_limit () Bool)
(declare-fun c2b40e0c6_debt_accounting_executed_for_eth_sent () Bool)
(declare-fun c2b40e0c6_pool_initialized_at_tick_zero () Bool)
(declare-fun c2b40e0c6_victim_sqrt_ratio_limit_set_near_price () Bool)
(declare-fun c2b40e0c6_victim_swap_msg_value_eth () Int)
(assert
 (= c2b40e0c6_attacker_moved_price_to_victim_limit c2b40e0c6_attacker_moved_price_to_victim_limit))
(assert
 (= c2b40e0c6_debt_accounting_executed_for_eth_sent c2b40e0c6_debt_accounting_executed_for_eth_sent))
(assert
 (= c2b40e0c6_pool_initialized_at_tick_zero c2b40e0c6_pool_initialized_at_tick_zero))
(assert
 (= c2b40e0c6_victim_sqrt_ratio_limit_set_near_price c2b40e0c6_victim_sqrt_ratio_limit_set_near_price))
(assert
 (= c2b40e0c6_victim_swap_msg_value_eth c2b40e0c6_victim_swap_msg_value_eth))
(define-fun report_preconditions () Bool (and c2b40e0c6_pool_initialized_at_tick_zero
     (= 10 c2b40e0c6_victim_swap_msg_value_eth)
     c2b40e0c6_victim_sqrt_ratio_limit_set_near_price
     c2b40e0c6_attacker_moved_price_to_victim_limit))
(define-fun report_safety () Bool (=> c2b40e0c6_attacker_moved_price_to_victim_limit
    (=> (and (< 0 c2b40e0c6_victim_swap_msg_value_eth)
             c2b40e0c6_victim_sqrt_ratio_limit_set_near_price)
        c2b40e0c6_debt_accounting_executed_for_eth_sent)))
(define-fun report_effects () Bool (and c2b40e0c6_attacker_moved_price_to_victim_limit
     (< 0 c2b40e0c6_victim_swap_msg_value_eth)
     c2b40e0c6_victim_sqrt_ratio_limit_set_near_price
     (not c2b40e0c6_debt_accounting_executed_for_eth_sent)))
(assert report_preconditions)
(check-sat)
(get-model)
