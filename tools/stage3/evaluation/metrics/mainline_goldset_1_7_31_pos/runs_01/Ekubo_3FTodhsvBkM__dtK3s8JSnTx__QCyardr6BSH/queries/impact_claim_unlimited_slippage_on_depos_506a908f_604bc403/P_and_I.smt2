; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c103d0cb5_deposit_settlement_occurs () Bool)
(declare-fun c103d0cb5_final_debt0 () Int)
(declare-fun c103d0cb5_final_debt1 () Int)
(declare-fun c103d0cb5_liquidity_l () Int)
(declare-fun c103d0cb5_max_amount0 () Int)
(declare-fun c103d0cb5_max_amount1 () Int)
(assert
 (= c103d0cb5_deposit_settlement_occurs c103d0cb5_deposit_settlement_occurs))
(assert
 (= c103d0cb5_final_debt0 c103d0cb5_final_debt0))
(assert
 (= c103d0cb5_final_debt1 c103d0cb5_final_debt1))
(assert
 (= c103d0cb5_liquidity_l c103d0cb5_liquidity_l))
(assert
 (= c103d0cb5_max_amount0 c103d0cb5_max_amount0))
(assert
 (= c103d0cb5_max_amount1 c103d0cb5_max_amount1))
(define-fun report_preconditions () Bool (and (<= 0 c103d0cb5_max_amount0)
     (<= 0 c103d0cb5_max_amount1)
     (<= 0 c103d0cb5_liquidity_l)
     c103d0cb5_deposit_settlement_occurs))
(define-fun report_safety () Bool (<= c103d0cb5_final_debt0 c103d0cb5_max_amount0))
(define-fun report_effects () Bool (and c103d0cb5_deposit_settlement_occurs
     (not (<= c103d0cb5_final_debt0 c103d0cb5_max_amount0))
     (or (> c103d0cb5_final_debt0 c103d0cb5_max_amount0)
         (> c103d0cb5_final_debt1 c103d0cb5_max_amount1))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
