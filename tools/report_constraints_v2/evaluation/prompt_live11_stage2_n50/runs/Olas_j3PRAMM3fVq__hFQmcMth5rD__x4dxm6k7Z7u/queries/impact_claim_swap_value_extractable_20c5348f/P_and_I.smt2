; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c51d4de22_amount_out_minimum () Int)
(declare-fun c51d4de22_effective_slippage_bound_enforced () Bool)
(declare-fun c51d4de22_post_swap_validation_present () Bool)
(declare-fun c51d4de22_sqrt_price_limit_x96 () Int)
(declare-fun c51d4de22_swap_value_extractable () Bool)
(assert
 (= c51d4de22_amount_out_minimum c51d4de22_amount_out_minimum))
(assert
 (= c51d4de22_effective_slippage_bound_enforced c51d4de22_effective_slippage_bound_enforced))
(assert
 (= c51d4de22_post_swap_validation_present c51d4de22_post_swap_validation_present))
(assert
 (= c51d4de22_sqrt_price_limit_x96 c51d4de22_sqrt_price_limit_x96))
(assert
 (= c51d4de22_swap_value_extractable c51d4de22_swap_value_extractable))
(define-fun report_preconditions () Bool (and (= 1 c51d4de22_amount_out_minimum)
     (= 0 c51d4de22_sqrt_price_limit_x96)
     (not c51d4de22_post_swap_validation_present)))
(define-fun report_safety () Bool (=> (and (= 1 c51d4de22_amount_out_minimum)
         (= 0 c51d4de22_sqrt_price_limit_x96)
         (not c51d4de22_post_swap_validation_present))
    (and c51d4de22_effective_slippage_bound_enforced
         (not c51d4de22_swap_value_extractable))))
(define-fun report_effects () Bool (and (= 1 c51d4de22_amount_out_minimum)
     (= 0 c51d4de22_sqrt_price_limit_x96)
     (not c51d4de22_post_swap_validation_present)
     (not (and c51d4de22_effective_slippage_bound_enforced
               (not c51d4de22_swap_value_extractable)))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
