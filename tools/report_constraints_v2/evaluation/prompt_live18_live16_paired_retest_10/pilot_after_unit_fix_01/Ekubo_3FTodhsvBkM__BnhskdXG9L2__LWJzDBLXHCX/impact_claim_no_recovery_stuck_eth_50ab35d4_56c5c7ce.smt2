; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc358e1c5_attacker_front_run_moves_price_to_limit () Bool)
(declare-fun cc358e1c5_debt_accounting_executed_for_eth () Bool)
(declare-fun cc358e1c5_pool_initialized_at_tick_zero () Bool)
(declare-fun cc358e1c5_stuck_eth_extractable () Bool)
(declare-fun cc358e1c5_victim_sqrt_ratio_limit_set_near_price () Bool)
(declare-fun cc358e1c5_victim_swap_msg_value_eth () Int)
(assert
 (= cc358e1c5_attacker_front_run_moves_price_to_limit cc358e1c5_attacker_front_run_moves_price_to_limit))
(assert
 (= cc358e1c5_debt_accounting_executed_for_eth cc358e1c5_debt_accounting_executed_for_eth))
(assert
 (= cc358e1c5_pool_initialized_at_tick_zero cc358e1c5_pool_initialized_at_tick_zero))
(assert
 (= cc358e1c5_stuck_eth_extractable cc358e1c5_stuck_eth_extractable))
(assert
 (= cc358e1c5_victim_sqrt_ratio_limit_set_near_price cc358e1c5_victim_sqrt_ratio_limit_set_near_price))
(assert
 (= cc358e1c5_victim_swap_msg_value_eth cc358e1c5_victim_swap_msg_value_eth))
(define-fun report_preconditions () Bool (and cc358e1c5_pool_initialized_at_tick_zero
     cc358e1c5_victim_sqrt_ratio_limit_set_near_price
     (= 10 cc358e1c5_victim_swap_msg_value_eth)
     cc358e1c5_attacker_front_run_moves_price_to_limit))
(define-fun report_safety () Bool (=> (not cc358e1c5_stuck_eth_extractable)
    (=> (and cc358e1c5_pool_initialized_at_tick_zero
             cc358e1c5_victim_sqrt_ratio_limit_set_near_price
             (= 10 cc358e1c5_victim_swap_msg_value_eth))
        cc358e1c5_debt_accounting_executed_for_eth)))
(define-fun report_effects () Bool (and (not cc358e1c5_stuck_eth_extractable)
     cc358e1c5_pool_initialized_at_tick_zero
     cc358e1c5_victim_sqrt_ratio_limit_set_near_price
     (= 10 cc358e1c5_victim_swap_msg_value_eth)
     (not cc358e1c5_debt_accounting_executed_for_eth)))
