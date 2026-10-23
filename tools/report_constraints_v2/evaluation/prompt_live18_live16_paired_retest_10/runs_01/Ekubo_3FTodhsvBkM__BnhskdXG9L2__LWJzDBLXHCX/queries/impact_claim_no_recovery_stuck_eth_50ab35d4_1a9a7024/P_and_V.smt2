; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cfe3027ef_eth_silently_accepted_without_accounting_or_refund () Bool)
(declare-fun cfe3027ef_pool_initialized_at_tick_zero () Bool)
(declare-fun cfe3027ef_stuck_eth_extractable () Bool)
(declare-fun cfe3027ef_swap_is_noop_with_value () Bool)
(declare-fun cfe3027ef_victim_msg_value_wei () Int)
(declare-fun cfe3027ef_victim_sqrt_ratio_limit_set_near_price () Bool)
(assert
 (= cfe3027ef_eth_silently_accepted_without_accounting_or_refund cfe3027ef_eth_silently_accepted_without_accounting_or_refund))
(assert
 (= cfe3027ef_pool_initialized_at_tick_zero cfe3027ef_pool_initialized_at_tick_zero))
(assert
 (= cfe3027ef_stuck_eth_extractable cfe3027ef_stuck_eth_extractable))
(assert
 (= cfe3027ef_swap_is_noop_with_value cfe3027ef_swap_is_noop_with_value))
(assert
 (= cfe3027ef_victim_msg_value_wei cfe3027ef_victim_msg_value_wei))
(assert
 (= cfe3027ef_victim_sqrt_ratio_limit_set_near_price cfe3027ef_victim_sqrt_ratio_limit_set_near_price))
(define-fun report_preconditions () Bool (and cfe3027ef_pool_initialized_at_tick_zero
     (= 10000000000000000000 cfe3027ef_victim_msg_value_wei)
     cfe3027ef_victim_sqrt_ratio_limit_set_near_price))
(define-fun report_safety () Bool (=> (not cfe3027ef_stuck_eth_extractable)
    (=> (and cfe3027ef_swap_is_noop_with_value
             (< 0 cfe3027ef_victim_msg_value_wei))
        (not cfe3027ef_eth_silently_accepted_without_accounting_or_refund))))
(define-fun report_effects () Bool (and (not cfe3027ef_stuck_eth_extractable)
     cfe3027ef_swap_is_noop_with_value
     (< 0 cfe3027ef_victim_msg_value_wei)
     (not (not cfe3027ef_eth_silently_accepted_without_accounting_or_refund))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
