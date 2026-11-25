; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4059b5b8_actual_amount0_charged () Int)
(declare-fun c4059b5b8_liquidity_l () Int)
(declare-fun c4059b5b8_max_amount0 () Int)
(declare-fun c4059b5b8_max_amount1 () Int)
(declare-fun c4059b5b8_unlimited_slippage_exposed () Bool)
(assert
 (= c4059b5b8_actual_amount0_charged c4059b5b8_actual_amount0_charged))
(assert
 (= c4059b5b8_liquidity_l c4059b5b8_liquidity_l))
(assert
 (= c4059b5b8_max_amount0 c4059b5b8_max_amount0))
(assert
 (= c4059b5b8_max_amount1 c4059b5b8_max_amount1))
(assert
 (= c4059b5b8_unlimited_slippage_exposed c4059b5b8_unlimited_slippage_exposed))
(define-fun report_preconditions () Bool (and (<= 0 c4059b5b8_max_amount0)
     (<= 0 c4059b5b8_max_amount1)
     (<= 0 c4059b5b8_liquidity_l)
     c4059b5b8_unlimited_slippage_exposed))
(define-fun report_safety () Bool (<= c4059b5b8_actual_amount0_charged c4059b5b8_max_amount0))
(define-fun report_effects () Bool (and c4059b5b8_unlimited_slippage_exposed
     (not (<= c4059b5b8_actual_amount0_charged c4059b5b8_max_amount0))
     c4059b5b8_unlimited_slippage_exposed))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
