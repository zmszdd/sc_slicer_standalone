; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c90e72e05_base_is_power_of_two () Bool)
(declare-fun c90e72e05_impact_base_amount () Int)
(declare-fun c90e72e05_impact_quote_amount () Int)
(declare-fun c90e72e05_match_reverted_as_zero_cost () Bool)
(declare-fun c90e72e05_quote_less_than_base () Bool)
(assert
 (= c90e72e05_base_is_power_of_two c90e72e05_base_is_power_of_two))
(assert
 (= c90e72e05_impact_base_amount c90e72e05_impact_base_amount))
(assert
 (= c90e72e05_impact_quote_amount c90e72e05_impact_quote_amount))
(assert
 (= c90e72e05_match_reverted_as_zero_cost c90e72e05_match_reverted_as_zero_cost))
(assert
 (= c90e72e05_quote_less_than_base c90e72e05_quote_less_than_base))
(define-fun report_preconditions () Bool (and c90e72e05_base_is_power_of_two c90e72e05_quote_less_than_base))
(define-fun report_safety () Bool (=> (and c90e72e05_base_is_power_of_two c90e72e05_quote_less_than_base)
    (not c90e72e05_match_reverted_as_zero_cost)))
(define-fun report_effects () Bool (and c90e72e05_base_is_power_of_two
     c90e72e05_quote_less_than_base
     c90e72e05_match_reverted_as_zero_cost
     (= 1024 c90e72e05_impact_base_amount)
     (<= 1 c90e72e05_impact_quote_amount)
     (>= 1023 c90e72e05_impact_quote_amount)
     c90e72e05_match_reverted_as_zero_cost
     (= 1024 c90e72e05_impact_base_amount)
     (<= 1 c90e72e05_impact_quote_amount)
     (>= 1023 c90e72e05_impact_quote_amount)))
(assert report_preconditions)
(check-sat)
(get-model)
