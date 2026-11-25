; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cf7c82bcd_actual_amount0_charged () Int)
(declare-fun cf7c82bcd_actual_amount1_charged () Int)
(declare-fun cf7c82bcd_liquidity_l () Int)
(declare-fun cf7c82bcd_price_moved_unfavorably () Bool)
(declare-fun cf7c82bcd_user_max_amount0 () Int)
(declare-fun cf7c82bcd_user_max_amount1 () Int)
(assert
 (= cf7c82bcd_actual_amount0_charged cf7c82bcd_actual_amount0_charged))
(assert
 (= cf7c82bcd_actual_amount1_charged cf7c82bcd_actual_amount1_charged))
(assert
 (= cf7c82bcd_liquidity_l cf7c82bcd_liquidity_l))
(assert
 (= cf7c82bcd_price_moved_unfavorably cf7c82bcd_price_moved_unfavorably))
(assert
 (= cf7c82bcd_user_max_amount0 cf7c82bcd_user_max_amount0))
(assert
 (= cf7c82bcd_user_max_amount1 cf7c82bcd_user_max_amount1))
(define-fun report_preconditions () Bool (and (<= 0 cf7c82bcd_user_max_amount0)
     (<= 0 cf7c82bcd_user_max_amount1)
     (<= 0 cf7c82bcd_liquidity_l)
     cf7c82bcd_price_moved_unfavorably))
(define-fun report_safety () Bool (<= cf7c82bcd_actual_amount0_charged cf7c82bcd_user_max_amount0))
(define-fun report_effects () Bool (and cf7c82bcd_price_moved_unfavorably
     (not (<= cf7c82bcd_actual_amount0_charged cf7c82bcd_user_max_amount0))
     cf7c82bcd_price_moved_unfavorably
     (or (> cf7c82bcd_actual_amount0_charged cf7c82bcd_user_max_amount0)
         (> cf7c82bcd_actual_amount1_charged cf7c82bcd_user_max_amount1))
     cf7c82bcd_price_moved_unfavorably))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
