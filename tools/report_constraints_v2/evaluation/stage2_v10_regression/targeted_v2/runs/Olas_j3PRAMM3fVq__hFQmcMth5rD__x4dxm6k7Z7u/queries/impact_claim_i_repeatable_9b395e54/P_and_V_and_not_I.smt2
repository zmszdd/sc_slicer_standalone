; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c40791f23_amount_out_minimum () Int)
(declare-fun c40791f23_every_v3_buyback_exploitable () Bool)
(declare-fun c40791f23_mempool_public () Bool)
(declare-fun c40791f23_post_swap_validation_present () Bool)
(declare-fun c40791f23_sqrt_price_limit_x96 () Int)
(declare-fun c40791f23_swap_executes_at_inflated_price () Bool)
(assert
 (= c40791f23_amount_out_minimum c40791f23_amount_out_minimum))
(assert
 (= c40791f23_every_v3_buyback_exploitable c40791f23_every_v3_buyback_exploitable))
(assert
 (= c40791f23_mempool_public c40791f23_mempool_public))
(assert
 (= c40791f23_post_swap_validation_present c40791f23_post_swap_validation_present))
(assert
 (= c40791f23_sqrt_price_limit_x96 c40791f23_sqrt_price_limit_x96))
(assert
 (= c40791f23_swap_executes_at_inflated_price c40791f23_swap_executes_at_inflated_price))
(define-fun report_preconditions () Bool (and c40791f23_mempool_public
     (= 1 c40791f23_amount_out_minimum)
     (= 0 c40791f23_sqrt_price_limit_x96)
     (not c40791f23_post_swap_validation_present)))
(define-fun report_safety () Bool (=> (and c40791f23_mempool_public
         (= 1 c40791f23_amount_out_minimum)
         (= 0 c40791f23_sqrt_price_limit_x96)
         (not c40791f23_post_swap_validation_present))
    (and (not c40791f23_swap_executes_at_inflated_price)
         (not c40791f23_every_v3_buyback_exploitable))))
(define-fun report_effects () Bool (and c40791f23_mempool_public
     (= 1 c40791f23_amount_out_minimum)
     (= 0 c40791f23_sqrt_price_limit_x96)
     (not c40791f23_post_swap_validation_present)
     (not (and (not c40791f23_swap_executes_at_inflated_price)
               (not c40791f23_every_v3_buyback_exploitable)))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
