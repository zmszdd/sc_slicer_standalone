; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c705f353b_eth_stuck_no_recovery () Bool)
(declare-fun c705f353b_pool_has_liquidity () Bool)
(declare-fun c705f353b_pool_initialized_tick () Int)
(declare-fun c705f353b_price_moved_to_limit () Bool)
(declare-fun c705f353b_victim_msg_value () Int)
(declare-fun c705f353b_victim_sqrt_ratio_limit_set () Bool)
(assert
 (= c705f353b_eth_stuck_no_recovery c705f353b_eth_stuck_no_recovery))
(assert
 (= c705f353b_pool_has_liquidity c705f353b_pool_has_liquidity))
(assert
 (= c705f353b_pool_initialized_tick c705f353b_pool_initialized_tick))
(assert
 (= c705f353b_price_moved_to_limit c705f353b_price_moved_to_limit))
(assert
 (= c705f353b_victim_msg_value c705f353b_victim_msg_value))
(assert
 (= c705f353b_victim_sqrt_ratio_limit_set c705f353b_victim_sqrt_ratio_limit_set))
(define-fun report_preconditions () Bool (and (= 0 c705f353b_pool_initialized_tick)
     c705f353b_pool_has_liquidity
     c705f353b_victim_sqrt_ratio_limit_set
     (= 10 c705f353b_victim_msg_value)
     c705f353b_price_moved_to_limit))
(define-fun report_safety () Bool (=> c705f353b_eth_stuck_no_recovery
    (=> (and (< 0 c705f353b_victim_msg_value)
             c705f353b_victim_sqrt_ratio_limit_set)
        (not c705f353b_eth_stuck_no_recovery))))
(define-fun report_effects () Bool (and c705f353b_eth_stuck_no_recovery
     (< 0 c705f353b_victim_msg_value)
     c705f353b_victim_sqrt_ratio_limit_set
     (not (not c705f353b_eth_stuck_no_recovery))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
