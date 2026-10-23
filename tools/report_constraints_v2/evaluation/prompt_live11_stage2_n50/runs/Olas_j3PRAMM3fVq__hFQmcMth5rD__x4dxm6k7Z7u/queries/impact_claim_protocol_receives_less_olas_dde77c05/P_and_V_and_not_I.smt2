; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c491df97f_amount_out_min () Int)
(declare-fun c491df97f_effective_min_out_bound_present () Bool)
(declare-fun c491df97f_olas_fair_value () Int)
(declare-fun c491df97f_olas_received () Int)
(declare-fun c491df97f_post_swap_validation_present () Bool)
(declare-fun c491df97f_sqrt_price_limit_x96 () Int)
(assert
 (= c491df97f_amount_out_min c491df97f_amount_out_min))
(assert
 (= c491df97f_effective_min_out_bound_present c491df97f_effective_min_out_bound_present))
(assert
 (= c491df97f_olas_fair_value c491df97f_olas_fair_value))
(assert
 (= c491df97f_olas_received c491df97f_olas_received))
(assert
 (= c491df97f_post_swap_validation_present c491df97f_post_swap_validation_present))
(assert
 (= c491df97f_sqrt_price_limit_x96 c491df97f_sqrt_price_limit_x96))
(define-fun report_preconditions () Bool (and (= 1 c491df97f_amount_out_min)
     (= 0 c491df97f_sqrt_price_limit_x96)
     (not c491df97f_post_swap_validation_present)))
(define-fun report_safety () Bool (=> (and (= 1 c491df97f_amount_out_min)
         (= 0 c491df97f_sqrt_price_limit_x96)
         (not c491df97f_post_swap_validation_present))
    (and c491df97f_effective_min_out_bound_present
         (>= c491df97f_olas_received c491df97f_olas_fair_value))))
(define-fun report_effects () Bool (and (= 1 c491df97f_amount_out_min)
     (= 0 c491df97f_sqrt_price_limit_x96)
     (not c491df97f_post_swap_validation_present)
     (not (and c491df97f_effective_min_out_bound_present
               (>= c491df97f_olas_received c491df97f_olas_fair_value)))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
