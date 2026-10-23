; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca6ebb27d_amounts_disjoint_bits () Bool)
(declare-fun ca6ebb27d_base_is_power_of_two () Bool)
(declare-fun ca6ebb27d_quote_less_than_base () Bool)
(declare-fun ca6ebb27d_zero_cost_trade_reverted () Bool)
(assert
 (= ca6ebb27d_amounts_disjoint_bits ca6ebb27d_amounts_disjoint_bits))
(assert
 (= ca6ebb27d_base_is_power_of_two ca6ebb27d_base_is_power_of_two))
(assert
 (= ca6ebb27d_quote_less_than_base ca6ebb27d_quote_less_than_base))
(assert
 (= ca6ebb27d_zero_cost_trade_reverted ca6ebb27d_zero_cost_trade_reverted))
(define-fun report_preconditions () Bool (and ca6ebb27d_amounts_disjoint_bits
     ca6ebb27d_base_is_power_of_two
     ca6ebb27d_quote_less_than_base))
(define-fun report_safety () Bool (=> ca6ebb27d_zero_cost_trade_reverted
    (=> (and ca6ebb27d_amounts_disjoint_bits
             ca6ebb27d_base_is_power_of_two
             ca6ebb27d_quote_less_than_base)
        (not ca6ebb27d_zero_cost_trade_reverted))))
(define-fun report_effects () Bool (and ca6ebb27d_zero_cost_trade_reverted
     ca6ebb27d_amounts_disjoint_bits
     ca6ebb27d_base_is_power_of_two
     ca6ebb27d_quote_less_than_base
     (not (not ca6ebb27d_zero_cost_trade_reverted))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
