; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce59242dc_limit_order_match_in_progress () Bool)
(declare-fun ce59242dc_matched_amounts_disjoint_bits () Bool)
(declare-fun ce59242dc_one_side_receives_without_sending () Bool)
(declare-fun ce59242dc_traders_encounter_unexplained_failures_occurred () Bool)
(declare-fun ce59242dc_zero_cost_guard_triggered () Bool)
(assert
 (= ce59242dc_limit_order_match_in_progress ce59242dc_limit_order_match_in_progress))
(assert
 (= ce59242dc_matched_amounts_disjoint_bits ce59242dc_matched_amounts_disjoint_bits))
(assert
 (= ce59242dc_one_side_receives_without_sending ce59242dc_one_side_receives_without_sending))
(assert
 (= ce59242dc_traders_encounter_unexplained_failures_occurred ce59242dc_traders_encounter_unexplained_failures_occurred))
(assert
 (= ce59242dc_zero_cost_guard_triggered ce59242dc_zero_cost_guard_triggered))
(define-fun report_preconditions () Bool (and ce59242dc_limit_order_match_in_progress
     ce59242dc_matched_amounts_disjoint_bits))
(define-fun report_safety () Bool (=> ce59242dc_limit_order_match_in_progress
    (and ce59242dc_zero_cost_guard_triggered
         ce59242dc_one_side_receives_without_sending)))
(define-fun report_effects () Bool ce59242dc_traders_encounter_unexplained_failures_occurred)
(assert report_preconditions)
(check-sat)
(get-model)
