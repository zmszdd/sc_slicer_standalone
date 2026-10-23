; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cac82f860_eth_recovery_mechanism_exists () Bool)
(declare-fun cac82f860_eth_stuck_forever () Bool)
(declare-fun cac82f860_pool_initialized_at_tick_zero () Bool)
(declare-fun cac82f860_victim_eth_sent_wei () Int)
(declare-fun cac82f860_victim_swap_submitted_with_sqrt_ratio_limit () Bool)
(assert
 (= cac82f860_eth_recovery_mechanism_exists cac82f860_eth_recovery_mechanism_exists))
(assert
 (= cac82f860_eth_stuck_forever cac82f860_eth_stuck_forever))
(assert
 (= cac82f860_pool_initialized_at_tick_zero cac82f860_pool_initialized_at_tick_zero))
(assert
 (= cac82f860_victim_eth_sent_wei cac82f860_victim_eth_sent_wei))
(assert
 (= cac82f860_victim_swap_submitted_with_sqrt_ratio_limit cac82f860_victim_swap_submitted_with_sqrt_ratio_limit))
(define-fun report_preconditions () Bool (and cac82f860_pool_initialized_at_tick_zero
     cac82f860_victim_swap_submitted_with_sqrt_ratio_limit
     (= 10 cac82f860_victim_eth_sent_wei)))
(define-fun report_safety () Bool (=> cac82f860_victim_swap_submitted_with_sqrt_ratio_limit
    cac82f860_eth_recovery_mechanism_exists))
(define-fun report_effects () Bool (and cac82f860_eth_stuck_forever cac82f860_eth_stuck_forever))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
