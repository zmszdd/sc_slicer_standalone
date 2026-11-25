; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8b911ca3_final_debt0 () Int)
(declare-fun c8b911ca3_final_debt1 () Int)
(declare-fun c8b911ca3_liquidity_l () Int)
(declare-fun c8b911ca3_max_amount0 () Int)
(declare-fun c8b911ca3_max_amount1 () Int)
(declare-fun c8b911ca3_price_moved_unfavorably () Bool)
(assert
 (= c8b911ca3_final_debt0 c8b911ca3_final_debt0))
(assert
 (= c8b911ca3_final_debt1 c8b911ca3_final_debt1))
(assert
 (= c8b911ca3_liquidity_l c8b911ca3_liquidity_l))
(assert
 (= c8b911ca3_max_amount0 c8b911ca3_max_amount0))
(assert
 (= c8b911ca3_max_amount1 c8b911ca3_max_amount1))
(assert
 (= c8b911ca3_price_moved_unfavorably c8b911ca3_price_moved_unfavorably))
(define-fun report_preconditions () Bool (and (<= 0 c8b911ca3_max_amount0)
     (<= 0 c8b911ca3_max_amount1)
     (<= 0 c8b911ca3_liquidity_l)
     c8b911ca3_price_moved_unfavorably))
(define-fun report_safety () Bool (<= c8b911ca3_final_debt0 c8b911ca3_max_amount0))
(define-fun report_effects () Bool (and c8b911ca3_price_moved_unfavorably
     (not (<= c8b911ca3_final_debt0 c8b911ca3_max_amount0))
     (or (> c8b911ca3_final_debt0 c8b911ca3_max_amount0)
         (> c8b911ca3_final_debt1 c8b911ca3_max_amount1))
     c8b911ca3_price_moved_unfavorably))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
