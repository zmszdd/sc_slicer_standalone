; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c68354a41_amount_out_minimum () Int)
(declare-fun c68354a41_buyback_pending_in_mempool () Bool)
(declare-fun c68354a41_effective_min_output_bound_enforced () Bool)
(declare-fun c68354a41_post_swap_validation_present () Bool)
(declare-fun c68354a41_sqrt_price_limit_x96 () Int)
(declare-fun c68354a41_victim_receives_minimal_olas () Bool)
(assert
 (= c68354a41_amount_out_minimum c68354a41_amount_out_minimum))
(assert
 (= c68354a41_buyback_pending_in_mempool c68354a41_buyback_pending_in_mempool))
(assert
 (= c68354a41_effective_min_output_bound_enforced c68354a41_effective_min_output_bound_enforced))
(assert
 (= c68354a41_post_swap_validation_present c68354a41_post_swap_validation_present))
(assert
 (= c68354a41_sqrt_price_limit_x96 c68354a41_sqrt_price_limit_x96))
(assert
 (= c68354a41_victim_receives_minimal_olas c68354a41_victim_receives_minimal_olas))
(define-fun report_preconditions () Bool (and (= 1 c68354a41_amount_out_minimum)
     (= 0 c68354a41_sqrt_price_limit_x96)
     (not c68354a41_post_swap_validation_present)
     c68354a41_buyback_pending_in_mempool))
(define-fun report_safety () Bool (=> (and (= 1 c68354a41_amount_out_minimum)
         (= 0 c68354a41_sqrt_price_limit_x96)
         (not c68354a41_post_swap_validation_present))
    (or c68354a41_effective_min_output_bound_enforced
        (not c68354a41_victim_receives_minimal_olas))))
(define-fun report_effects () Bool (and (= 1 c68354a41_amount_out_minimum)
     (= 0 c68354a41_sqrt_price_limit_x96)
     (not c68354a41_post_swap_validation_present)
     (not (or c68354a41_effective_min_output_bound_enforced
              (not c68354a41_victim_receives_minimal_olas)))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
