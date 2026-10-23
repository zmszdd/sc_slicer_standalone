; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c97247839_attacker_moved_price_to_limit () Bool)
(declare-fun c97247839_pool_initialized_at_tick_zero () Bool)
(declare-fun c97247839_swap_is_noop_with_value () Bool)
(declare-fun c97247839_victim_msg_value () Int)
(declare-fun c97247839_victim_sqrt_ratio_limit () Int)
(assert
 (= c97247839_attacker_moved_price_to_limit c97247839_attacker_moved_price_to_limit))
(assert
 (= c97247839_pool_initialized_at_tick_zero c97247839_pool_initialized_at_tick_zero))
(assert
 (= c97247839_swap_is_noop_with_value c97247839_swap_is_noop_with_value))
(assert
 (= c97247839_victim_msg_value c97247839_victim_msg_value))
(assert
 (= c97247839_victim_sqrt_ratio_limit c97247839_victim_sqrt_ratio_limit))
(define-fun report_preconditions () Bool (and c97247839_pool_initialized_at_tick_zero
     (< 0 c97247839_victim_msg_value)
     (< 0 c97247839_victim_sqrt_ratio_limit)
     c97247839_attacker_moved_price_to_limit))
(define-fun report_safety () Bool (=> c97247839_attacker_moved_price_to_limit
    (=> (and c97247839_pool_initialized_at_tick_zero
             (< 0 c97247839_victim_msg_value))
        (not c97247839_swap_is_noop_with_value))))
(define-fun report_effects () Bool (and c97247839_attacker_moved_price_to_limit
     c97247839_pool_initialized_at_tick_zero
     (< 0 c97247839_victim_msg_value)
     (not (not c97247839_swap_is_noop_with_value))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
