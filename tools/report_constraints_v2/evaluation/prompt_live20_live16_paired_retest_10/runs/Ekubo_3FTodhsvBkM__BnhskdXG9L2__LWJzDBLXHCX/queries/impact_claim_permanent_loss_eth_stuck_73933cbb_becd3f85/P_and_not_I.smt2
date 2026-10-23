; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c80102ccf_eth_stuck_forever () Bool)
(declare-fun c80102ccf_msg_value_positive () Bool)
(declare-fun c80102ccf_pool_initialized_at_tick_zero () Bool)
(declare-fun c80102ccf_sqrt_ratio_equals_limit () Bool)
(declare-fun c80102ccf_swap_reverted () Bool)
(declare-fun c80102ccf_victim_msg_value_eth () Int)
(assert
 (= c80102ccf_eth_stuck_forever c80102ccf_eth_stuck_forever))
(assert
 (= c80102ccf_msg_value_positive c80102ccf_msg_value_positive))
(assert
 (= c80102ccf_pool_initialized_at_tick_zero c80102ccf_pool_initialized_at_tick_zero))
(assert
 (= c80102ccf_sqrt_ratio_equals_limit c80102ccf_sqrt_ratio_equals_limit))
(assert
 (= c80102ccf_swap_reverted c80102ccf_swap_reverted))
(assert
 (= c80102ccf_victim_msg_value_eth c80102ccf_victim_msg_value_eth))
(define-fun report_preconditions () Bool (and c80102ccf_pool_initialized_at_tick_zero
     (= 10 c80102ccf_victim_msg_value_eth)))
(define-fun report_safety () Bool (=> (and c80102ccf_sqrt_ratio_equals_limit c80102ccf_msg_value_positive)
    c80102ccf_swap_reverted))
(define-fun report_effects () Bool (and c80102ccf_eth_stuck_forever c80102ccf_eth_stuck_forever))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
