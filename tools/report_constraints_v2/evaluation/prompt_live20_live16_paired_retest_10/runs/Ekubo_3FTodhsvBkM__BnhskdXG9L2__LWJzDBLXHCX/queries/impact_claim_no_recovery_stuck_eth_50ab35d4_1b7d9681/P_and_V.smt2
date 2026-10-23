; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4907da66_debt_accounting_performed () Bool)
(declare-fun c4907da66_pool_initialized_at_tick_zero () Bool)
(declare-fun c4907da66_stuck_eth_extractable () Bool)
(declare-fun c4907da66_victim_sqrt_ratio_limit_near_price () Bool)
(declare-fun c4907da66_victim_swap_msg_value () Int)
(assert
 (= c4907da66_debt_accounting_performed c4907da66_debt_accounting_performed))
(assert
 (= c4907da66_pool_initialized_at_tick_zero c4907da66_pool_initialized_at_tick_zero))
(assert
 (= c4907da66_stuck_eth_extractable c4907da66_stuck_eth_extractable))
(assert
 (= c4907da66_victim_sqrt_ratio_limit_near_price c4907da66_victim_sqrt_ratio_limit_near_price))
(assert
 (= c4907da66_victim_swap_msg_value c4907da66_victim_swap_msg_value))
(define-fun report_preconditions () Bool (and c4907da66_pool_initialized_at_tick_zero
     (= 10 c4907da66_victim_swap_msg_value)
     c4907da66_victim_sqrt_ratio_limit_near_price))
(define-fun report_safety () Bool (=> (< 0 c4907da66_victim_swap_msg_value) c4907da66_debt_accounting_performed))
(define-fun report_effects () Bool (not c4907da66_stuck_eth_extractable))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
