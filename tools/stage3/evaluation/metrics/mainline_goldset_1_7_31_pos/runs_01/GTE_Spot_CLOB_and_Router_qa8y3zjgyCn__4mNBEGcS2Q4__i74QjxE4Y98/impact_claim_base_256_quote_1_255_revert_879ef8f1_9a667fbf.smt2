; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1d9ebfa2_base_is_power_of_two () Bool)
(declare-fun c1d9ebfa2_impact_base_amount () Int)
(declare-fun c1d9ebfa2_impact_quote_amount () Int)
(declare-fun c1d9ebfa2_legitimate_disjoint_bits_trade () Bool)
(declare-fun c1d9ebfa2_quote_less_than_base () Bool)
(declare-fun c1d9ebfa2_zero_cost_check_reverts () Bool)
(assert
 (= c1d9ebfa2_base_is_power_of_two c1d9ebfa2_base_is_power_of_two))
(assert
 (= c1d9ebfa2_impact_base_amount c1d9ebfa2_impact_base_amount))
(assert
 (= c1d9ebfa2_impact_quote_amount c1d9ebfa2_impact_quote_amount))
(assert
 (= c1d9ebfa2_legitimate_disjoint_bits_trade c1d9ebfa2_legitimate_disjoint_bits_trade))
(assert
 (= c1d9ebfa2_quote_less_than_base c1d9ebfa2_quote_less_than_base))
(assert
 (= c1d9ebfa2_zero_cost_check_reverts c1d9ebfa2_zero_cost_check_reverts))
(define-fun report_preconditions () Bool (and c1d9ebfa2_base_is_power_of_two
     c1d9ebfa2_quote_less_than_base
     c1d9ebfa2_legitimate_disjoint_bits_trade))
(define-fun report_safety () Bool (not c1d9ebfa2_zero_cost_check_reverts))
(define-fun report_effects () Bool (and c1d9ebfa2_legitimate_disjoint_bits_trade
     c1d9ebfa2_zero_cost_check_reverts
     (= 256 c1d9ebfa2_impact_base_amount)
     (<= 1 c1d9ebfa2_impact_quote_amount)
     (>= 255 c1d9ebfa2_impact_quote_amount)
     c1d9ebfa2_zero_cost_check_reverts
     (= 256 c1d9ebfa2_impact_base_amount)
     (<= 1 c1d9ebfa2_impact_quote_amount)
     (>= 255 c1d9ebfa2_impact_quote_amount)))
