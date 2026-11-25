; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c482b3398_base_is_power_of_two () Bool)
(declare-fun c482b3398_false_zero_cost_revert_occurs () Bool)
(declare-fun c482b3398_impact_base_amount () Int)
(declare-fun c482b3398_impact_quote_amount () Int)
(declare-fun c482b3398_legitimate_trade_completes () Bool)
(declare-fun c482b3398_quote_less_than_base () Bool)
(assert
 (= c482b3398_base_is_power_of_two c482b3398_base_is_power_of_two))
(assert
 (= c482b3398_false_zero_cost_revert_occurs c482b3398_false_zero_cost_revert_occurs))
(assert
 (= c482b3398_impact_base_amount c482b3398_impact_base_amount))
(assert
 (= c482b3398_impact_quote_amount c482b3398_impact_quote_amount))
(assert
 (= c482b3398_legitimate_trade_completes c482b3398_legitimate_trade_completes))
(assert
 (= c482b3398_quote_less_than_base c482b3398_quote_less_than_base))
(define-fun report_preconditions () Bool (and c482b3398_base_is_power_of_two c482b3398_quote_less_than_base))
(define-fun report_safety () Bool (=> (and c482b3398_base_is_power_of_two c482b3398_quote_less_than_base)
    c482b3398_legitimate_trade_completes))
(define-fun report_effects () Bool (and c482b3398_base_is_power_of_two
     c482b3398_quote_less_than_base
     (not c482b3398_legitimate_trade_completes)
     (= 512 c482b3398_impact_base_amount)
     (<= 1 c482b3398_impact_quote_amount)
     (>= 511 c482b3398_impact_quote_amount)
     c482b3398_false_zero_cost_revert_occurs
     (= 512 c482b3398_impact_base_amount)
     (<= 1 c482b3398_impact_quote_amount)
     (>= 511 c482b3398_impact_quote_amount)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
