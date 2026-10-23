; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca301de2d_debt_accounting_performed () Bool)
(declare-fun ca301de2d_eth_sent_via_msg_value () Bool)
(declare-fun ca301de2d_eth_stuck_forever () Bool)
(declare-fun ca301de2d_pool_initialized_at_tick_zero () Bool)
(declare-fun ca301de2d_victim_sqrt_ratio_limit_near_price () Bool)
(declare-fun ca301de2d_victim_swap_msg_value_eth () Int)
(assert
 (= ca301de2d_debt_accounting_performed ca301de2d_debt_accounting_performed))
(assert
 (= ca301de2d_eth_sent_via_msg_value ca301de2d_eth_sent_via_msg_value))
(assert
 (= ca301de2d_eth_stuck_forever ca301de2d_eth_stuck_forever))
(assert
 (= ca301de2d_pool_initialized_at_tick_zero ca301de2d_pool_initialized_at_tick_zero))
(assert
 (= ca301de2d_victim_sqrt_ratio_limit_near_price ca301de2d_victim_sqrt_ratio_limit_near_price))
(assert
 (= ca301de2d_victim_swap_msg_value_eth ca301de2d_victim_swap_msg_value_eth))
(define-fun report_preconditions () Bool (and ca301de2d_pool_initialized_at_tick_zero
     (= 10 ca301de2d_victim_swap_msg_value_eth)
     ca301de2d_victim_sqrt_ratio_limit_near_price))
(define-fun report_safety () Bool (=> ca301de2d_eth_stuck_forever
    (=> ca301de2d_eth_sent_via_msg_value ca301de2d_debt_accounting_performed)))
(define-fun report_effects () Bool (and ca301de2d_eth_stuck_forever
     ca301de2d_eth_sent_via_msg_value
     (not ca301de2d_debt_accounting_performed)))
(assert report_preconditions)
(check-sat)
(get-model)
