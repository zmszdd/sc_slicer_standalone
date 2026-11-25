; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1d78b2f3_base_is_power_of_two () Bool)
(declare-fun c1d78b2f3_legitimate_trade_completes () Bool)
(declare-fun c1d78b2f3_matched_base_amount () Int)
(declare-fun c1d78b2f3_matched_quote_amount () Int)
(declare-fun c1d78b2f3_zero_cost_trade_revert_occurred () Bool)
(assert
 (= c1d78b2f3_base_is_power_of_two c1d78b2f3_base_is_power_of_two))
(assert
 (= c1d78b2f3_legitimate_trade_completes c1d78b2f3_legitimate_trade_completes))
(assert
 (= c1d78b2f3_matched_base_amount c1d78b2f3_matched_base_amount))
(assert
 (= c1d78b2f3_matched_quote_amount c1d78b2f3_matched_quote_amount))
(assert
 (= c1d78b2f3_zero_cost_trade_revert_occurred c1d78b2f3_zero_cost_trade_revert_occurred))
(define-fun report_preconditions () Bool (and c1d78b2f3_base_is_power_of_two
     (< c1d78b2f3_matched_quote_amount c1d78b2f3_matched_base_amount)))
(define-fun report_safety () Bool (=> (and c1d78b2f3_base_is_power_of_two
         (< c1d78b2f3_matched_quote_amount c1d78b2f3_matched_base_amount))
    c1d78b2f3_legitimate_trade_completes))
(define-fun report_effects () Bool (and c1d78b2f3_base_is_power_of_two
     (< c1d78b2f3_matched_quote_amount c1d78b2f3_matched_base_amount)
     (not c1d78b2f3_legitimate_trade_completes)
     c1d78b2f3_zero_cost_trade_revert_occurred))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
