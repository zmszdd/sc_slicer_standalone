; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c783479c9_final_debt0 () Int)
(declare-fun c783479c9_final_debt1 () Int)
(declare-fun c783479c9_liquidity_computed () Int)
(declare-fun c783479c9_max_amount0_limit () Int)
(declare-fun c783479c9_max_amount1_limit () Int)
(assert
 (= c783479c9_final_debt0 c783479c9_final_debt0))
(assert
 (= c783479c9_final_debt1 c783479c9_final_debt1))
(assert
 (= c783479c9_liquidity_computed c783479c9_liquidity_computed))
(assert
 (= c783479c9_max_amount0_limit c783479c9_max_amount0_limit))
(assert
 (= c783479c9_max_amount1_limit c783479c9_max_amount1_limit))
(define-fun report_preconditions () Bool (and (<= 0 c783479c9_max_amount0_limit)
     (<= 0 c783479c9_max_amount1_limit)
     (<= 0 c783479c9_liquidity_computed)))
(define-fun report_safety () Bool (=> (<= 0 c783479c9_liquidity_computed)
    (<= c783479c9_final_debt0 c783479c9_max_amount0_limit)))
(define-fun report_effects () Bool (and (<= 0 c783479c9_liquidity_computed)
     (not (<= c783479c9_final_debt0 c783479c9_max_amount0_limit))
     (or (> c783479c9_final_debt0 c783479c9_max_amount0_limit)
         (> c783479c9_final_debt1 c783479c9_max_amount1_limit))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
