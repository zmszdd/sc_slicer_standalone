; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c445a31ae_eth_accounted_or_reverted () Bool)
(declare-fun c445a31ae_pool_initialized_at_tick_zero () Bool)
(declare-fun c445a31ae_stuck_eth_extractable () Bool)
(declare-fun c445a31ae_victim_sqrt_ratio_limit_near_price () Bool)
(declare-fun c445a31ae_victim_swap_msg_value () Int)
(assert
 (= c445a31ae_eth_accounted_or_reverted c445a31ae_eth_accounted_or_reverted))
(assert
 (= c445a31ae_pool_initialized_at_tick_zero c445a31ae_pool_initialized_at_tick_zero))
(assert
 (= c445a31ae_stuck_eth_extractable c445a31ae_stuck_eth_extractable))
(assert
 (= c445a31ae_victim_sqrt_ratio_limit_near_price c445a31ae_victim_sqrt_ratio_limit_near_price))
(assert
 (= c445a31ae_victim_swap_msg_value c445a31ae_victim_swap_msg_value))
(define-fun report_preconditions () Bool (and c445a31ae_pool_initialized_at_tick_zero
     (= 10 c445a31ae_victim_swap_msg_value)
     c445a31ae_victim_sqrt_ratio_limit_near_price))
(define-fun report_safety () Bool (=> (not c445a31ae_stuck_eth_extractable)
    (=> (and c445a31ae_pool_initialized_at_tick_zero
             (< 0 c445a31ae_victim_swap_msg_value)
             c445a31ae_victim_sqrt_ratio_limit_near_price)
        c445a31ae_eth_accounted_or_reverted)))
(define-fun report_effects () Bool (and (not c445a31ae_stuck_eth_extractable)
     c445a31ae_pool_initialized_at_tick_zero
     (< 0 c445a31ae_victim_swap_msg_value)
     c445a31ae_victim_sqrt_ratio_limit_near_price
     (not c445a31ae_eth_accounted_or_reverted)))
(assert report_preconditions)
(check-sat)
(get-model)
