; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c90195f78_emissions_wedged_indefinitely () Bool)
(declare-fun c90195f78_pool_live_weight_is_zero () Bool)
(declare-fun c90195f78_total_weight_is_zero () Bool)
(assert
 (= c90195f78_emissions_wedged_indefinitely c90195f78_emissions_wedged_indefinitely))
(assert
 (= c90195f78_pool_live_weight_is_zero c90195f78_pool_live_weight_is_zero))
(assert
 (= c90195f78_total_weight_is_zero c90195f78_total_weight_is_zero))
(define-fun report_preconditions () Bool (and c90195f78_total_weight_is_zero c90195f78_pool_live_weight_is_zero))
(define-fun report_safety () Bool (=> (and c90195f78_total_weight_is_zero c90195f78_pool_live_weight_is_zero)
    (not c90195f78_emissions_wedged_indefinitely)))
(define-fun report_effects () Bool (and c90195f78_total_weight_is_zero
     c90195f78_pool_live_weight_is_zero
     (not (not c90195f78_emissions_wedged_indefinitely))))
(assert report_preconditions)
(check-sat)
(get-model)
