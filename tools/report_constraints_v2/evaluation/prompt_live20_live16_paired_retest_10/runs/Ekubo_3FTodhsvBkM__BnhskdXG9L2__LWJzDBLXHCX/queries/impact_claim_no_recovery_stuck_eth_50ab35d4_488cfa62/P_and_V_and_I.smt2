; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7b6b2670_eth_recovery_mechanism_exists () Bool)
(declare-fun c7b6b2670_pool_initialized_at_tick_zero () Bool)
(declare-fun c7b6b2670_stuck_eth_extractable () Bool)
(declare-fun c7b6b2670_victim_eth_sent_wei () Int)
(declare-fun c7b6b2670_victim_swap_submitted_with_sqrt_ratio_limit_near_price () Bool)
(assert
 (= c7b6b2670_eth_recovery_mechanism_exists c7b6b2670_eth_recovery_mechanism_exists))
(assert
 (= c7b6b2670_pool_initialized_at_tick_zero c7b6b2670_pool_initialized_at_tick_zero))
(assert
 (= c7b6b2670_stuck_eth_extractable c7b6b2670_stuck_eth_extractable))
(assert
 (= c7b6b2670_victim_eth_sent_wei c7b6b2670_victim_eth_sent_wei))
(assert
 (= c7b6b2670_victim_swap_submitted_with_sqrt_ratio_limit_near_price c7b6b2670_victim_swap_submitted_with_sqrt_ratio_limit_near_price))
(define-fun report_preconditions () Bool (and c7b6b2670_pool_initialized_at_tick_zero
     c7b6b2670_victim_swap_submitted_with_sqrt_ratio_limit_near_price
     (= 10 c7b6b2670_victim_eth_sent_wei)))
(define-fun report_safety () Bool (=> c7b6b2670_victim_swap_submitted_with_sqrt_ratio_limit_near_price
    c7b6b2670_eth_recovery_mechanism_exists))
(define-fun report_effects () Bool (not c7b6b2670_stuck_eth_extractable))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
(get-model)
