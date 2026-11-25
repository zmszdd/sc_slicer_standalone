; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8d5796ef_interaction_uses_non_market_prices () Bool)
(declare-fun c8d5796ef_prices_reflect_true_market_values () Bool)
(declare-fun c8d5796ef_protocol_on_optimism_l2 () Bool)
(declare-fun c8d5796ef_sequencer_downtime_occurred () Bool)
(assert
 (= c8d5796ef_interaction_uses_non_market_prices c8d5796ef_interaction_uses_non_market_prices))
(assert
 (= c8d5796ef_prices_reflect_true_market_values c8d5796ef_prices_reflect_true_market_values))
(assert
 (= c8d5796ef_protocol_on_optimism_l2 c8d5796ef_protocol_on_optimism_l2))
(assert
 (= c8d5796ef_sequencer_downtime_occurred c8d5796ef_sequencer_downtime_occurred))
(define-fun report_preconditions () Bool (and c8d5796ef_protocol_on_optimism_l2 c8d5796ef_sequencer_downtime_occurred))
(define-fun report_safety () Bool (=> c8d5796ef_protocol_on_optimism_l2
    c8d5796ef_prices_reflect_true_market_values))
(define-fun report_effects () Bool (and c8d5796ef_protocol_on_optimism_l2
     (not c8d5796ef_prices_reflect_true_market_values)
     c8d5796ef_interaction_uses_non_market_prices))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
