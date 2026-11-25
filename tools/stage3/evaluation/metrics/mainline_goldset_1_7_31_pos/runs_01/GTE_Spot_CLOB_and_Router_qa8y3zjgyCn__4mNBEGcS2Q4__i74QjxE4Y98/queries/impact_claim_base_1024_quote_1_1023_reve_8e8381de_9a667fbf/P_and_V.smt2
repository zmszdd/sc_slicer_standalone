; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd4dcb68a_base_is_power_of_two () Bool)
(declare-fun cd4dcb68a_false_zero_cost_revert_occurs () Bool)
(declare-fun cd4dcb68a_legitimate_trade_completes () Bool)
(declare-fun cd4dcb68a_matched_base_amount () Int)
(declare-fun cd4dcb68a_matched_quote_amount () Int)
(assert
 (= cd4dcb68a_base_is_power_of_two cd4dcb68a_base_is_power_of_two))
(assert
 (= cd4dcb68a_false_zero_cost_revert_occurs cd4dcb68a_false_zero_cost_revert_occurs))
(assert
 (= cd4dcb68a_legitimate_trade_completes cd4dcb68a_legitimate_trade_completes))
(assert
 (= cd4dcb68a_matched_base_amount cd4dcb68a_matched_base_amount))
(assert
 (= cd4dcb68a_matched_quote_amount cd4dcb68a_matched_quote_amount))
(define-fun report_preconditions () Bool (and cd4dcb68a_base_is_power_of_two
     (< cd4dcb68a_matched_quote_amount cd4dcb68a_matched_base_amount)))
(define-fun report_safety () Bool (=> (and cd4dcb68a_base_is_power_of_two
         (< cd4dcb68a_matched_quote_amount cd4dcb68a_matched_base_amount))
    cd4dcb68a_legitimate_trade_completes))
(define-fun report_effects () Bool (and cd4dcb68a_base_is_power_of_two
     (< cd4dcb68a_matched_quote_amount cd4dcb68a_matched_base_amount)
     (not cd4dcb68a_legitimate_trade_completes)
     cd4dcb68a_false_zero_cost_revert_occurs
     cd4dcb68a_false_zero_cost_revert_occurs))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
