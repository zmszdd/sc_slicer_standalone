; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c72ff08ce_debt_accounting_performed () Bool)
(declare-fun c72ff08ce_eth_sent_via_msg_value () Bool)
(declare-fun c72ff08ce_pool_initialized_at_tick_zero () Bool)
(declare-fun c72ff08ce_stuck_eth_extractable () Bool)
(declare-fun c72ff08ce_victim_sqrt_ratio_limit_near_price () Bool)
(declare-fun c72ff08ce_victim_swap_msg_value () Int)
(assert
 (= c72ff08ce_debt_accounting_performed c72ff08ce_debt_accounting_performed))
(assert
 (= c72ff08ce_eth_sent_via_msg_value c72ff08ce_eth_sent_via_msg_value))
(assert
 (= c72ff08ce_pool_initialized_at_tick_zero c72ff08ce_pool_initialized_at_tick_zero))
(assert
 (= c72ff08ce_stuck_eth_extractable c72ff08ce_stuck_eth_extractable))
(assert
 (= c72ff08ce_victim_sqrt_ratio_limit_near_price c72ff08ce_victim_sqrt_ratio_limit_near_price))
(assert
 (= c72ff08ce_victim_swap_msg_value c72ff08ce_victim_swap_msg_value))
(define-fun report_preconditions () Bool (and c72ff08ce_pool_initialized_at_tick_zero
     (= 10 c72ff08ce_victim_swap_msg_value)
     c72ff08ce_victim_sqrt_ratio_limit_near_price))
(define-fun report_safety () Bool (=> (not c72ff08ce_stuck_eth_extractable)
    (=> c72ff08ce_eth_sent_via_msg_value c72ff08ce_debt_accounting_performed)))
(define-fun report_effects () Bool (and (not c72ff08ce_stuck_eth_extractable)
     c72ff08ce_eth_sent_via_msg_value
     (not c72ff08ce_debt_accounting_performed)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
