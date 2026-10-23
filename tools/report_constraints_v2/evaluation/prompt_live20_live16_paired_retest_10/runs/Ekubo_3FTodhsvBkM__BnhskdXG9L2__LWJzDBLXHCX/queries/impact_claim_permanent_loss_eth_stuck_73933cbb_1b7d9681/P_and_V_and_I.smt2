; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd1c7a916_debt_accounting_performed () Bool)
(declare-fun cd1c7a916_eth_stuck_forever () Bool)
(declare-fun cd1c7a916_pool_initialized_at_tick_zero () Bool)
(declare-fun cd1c7a916_swap_msg_value_eth () Int)
(declare-fun cd1c7a916_victim_msg_value_eth () Int)
(declare-fun cd1c7a916_victim_swap_sqrt_ratio_limit_near_price () Bool)
(assert
 (= cd1c7a916_debt_accounting_performed cd1c7a916_debt_accounting_performed))
(assert
 (= cd1c7a916_eth_stuck_forever cd1c7a916_eth_stuck_forever))
(assert
 (= cd1c7a916_pool_initialized_at_tick_zero cd1c7a916_pool_initialized_at_tick_zero))
(assert
 (= cd1c7a916_swap_msg_value_eth cd1c7a916_swap_msg_value_eth))
(assert
 (= cd1c7a916_victim_msg_value_eth cd1c7a916_victim_msg_value_eth))
(assert
 (= cd1c7a916_victim_swap_sqrt_ratio_limit_near_price cd1c7a916_victim_swap_sqrt_ratio_limit_near_price))
(define-fun report_preconditions () Bool (and cd1c7a916_pool_initialized_at_tick_zero
     cd1c7a916_victim_swap_sqrt_ratio_limit_near_price
     (= 10 cd1c7a916_victim_msg_value_eth)))
(define-fun report_safety () Bool (=> (< 0 cd1c7a916_swap_msg_value_eth) cd1c7a916_debt_accounting_performed))
(define-fun report_effects () Bool (and cd1c7a916_eth_stuck_forever cd1c7a916_eth_stuck_forever))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
(get-model)
