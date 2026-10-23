; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c177c51fb_msg_value_nonzero () Bool)
(declare-fun c177c51fb_pool_initialized_at_tick_zero_with_liquidity () Bool)
(declare-fun c177c51fb_sent_eth_accounted_in_pair_debt () Bool)
(declare-fun c177c51fb_sqrt_ratio_limit_set_near_price () Bool)
(declare-fun c177c51fb_stuck_eth_extractable () Bool)
(assert
 (= c177c51fb_msg_value_nonzero c177c51fb_msg_value_nonzero))
(assert
 (= c177c51fb_pool_initialized_at_tick_zero_with_liquidity c177c51fb_pool_initialized_at_tick_zero_with_liquidity))
(assert
 (= c177c51fb_sent_eth_accounted_in_pair_debt c177c51fb_sent_eth_accounted_in_pair_debt))
(assert
 (= c177c51fb_sqrt_ratio_limit_set_near_price c177c51fb_sqrt_ratio_limit_set_near_price))
(assert
 (= c177c51fb_stuck_eth_extractable c177c51fb_stuck_eth_extractable))
(define-fun report_preconditions () Bool (and c177c51fb_sqrt_ratio_limit_set_near_price
     c177c51fb_msg_value_nonzero
     c177c51fb_pool_initialized_at_tick_zero_with_liquidity))
(define-fun report_safety () Bool (=> (not c177c51fb_stuck_eth_extractable)
    (=> c177c51fb_msg_value_nonzero
        (= c177c51fb_sent_eth_accounted_in_pair_debt
           c177c51fb_sent_eth_accounted_in_pair_debt))))
(define-fun report_effects () Bool (and (not c177c51fb_stuck_eth_extractable)
     c177c51fb_msg_value_nonzero
     (not (= c177c51fb_sent_eth_accounted_in_pair_debt
             c177c51fb_sent_eth_accounted_in_pair_debt))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
