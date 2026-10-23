; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c73df018e_attacker_moved_price_to_victim_limit () Bool)
(declare-fun c73df018e_debt_accounting_executed_for_eth_sent () Bool)
(declare-fun c73df018e_eth_sent_stuck_forever () Bool)
(declare-fun c73df018e_pool_initialized_at_tick_zero () Bool)
(declare-fun c73df018e_victim_sqrt_ratio_limit_set_near_price () Bool)
(declare-fun c73df018e_victim_swap_msg_value_eth () Int)
(assert
 (= c73df018e_attacker_moved_price_to_victim_limit c73df018e_attacker_moved_price_to_victim_limit))
(assert
 (= c73df018e_debt_accounting_executed_for_eth_sent c73df018e_debt_accounting_executed_for_eth_sent))
(assert
 (= c73df018e_eth_sent_stuck_forever c73df018e_eth_sent_stuck_forever))
(assert
 (= c73df018e_pool_initialized_at_tick_zero c73df018e_pool_initialized_at_tick_zero))
(assert
 (= c73df018e_victim_sqrt_ratio_limit_set_near_price c73df018e_victim_sqrt_ratio_limit_set_near_price))
(assert
 (= c73df018e_victim_swap_msg_value_eth c73df018e_victim_swap_msg_value_eth))
(define-fun report_preconditions () Bool (and c73df018e_pool_initialized_at_tick_zero
     (= 10 c73df018e_victim_swap_msg_value_eth)
     c73df018e_victim_sqrt_ratio_limit_set_near_price
     c73df018e_attacker_moved_price_to_victim_limit))
(define-fun report_safety () Bool (=> c73df018e_eth_sent_stuck_forever
    (=> (and c73df018e_pool_initialized_at_tick_zero
             (= 10 c73df018e_victim_swap_msg_value_eth)
             c73df018e_victim_sqrt_ratio_limit_set_near_price
             c73df018e_attacker_moved_price_to_victim_limit)
        c73df018e_debt_accounting_executed_for_eth_sent)))
(define-fun report_effects () Bool (and c73df018e_eth_sent_stuck_forever
     c73df018e_pool_initialized_at_tick_zero
     (= 10 c73df018e_victim_swap_msg_value_eth)
     c73df018e_victim_sqrt_ratio_limit_set_near_price
     c73df018e_attacker_moved_price_to_victim_limit
     (not c73df018e_debt_accounting_executed_for_eth_sent)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
