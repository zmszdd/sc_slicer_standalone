; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c205b8a94_base_is_power_of_two () Bool)
(declare-fun c205b8a94_matched_base_amount () Int)
(declare-fun c205b8a94_matched_quote_amount () Int)
(declare-fun c205b8a94_zero_cost_trade_revert_occurred () Bool)
(assert
 (= c205b8a94_base_is_power_of_two c205b8a94_base_is_power_of_two))
(assert
 (= c205b8a94_matched_base_amount c205b8a94_matched_base_amount))
(assert
 (= c205b8a94_matched_quote_amount c205b8a94_matched_quote_amount))
(assert
 (= c205b8a94_zero_cost_trade_revert_occurred c205b8a94_zero_cost_trade_revert_occurred))
(define-fun report_preconditions () Bool (and c205b8a94_base_is_power_of_two
     (< c205b8a94_matched_quote_amount c205b8a94_matched_base_amount)))
(define-fun report_safety () Bool (=> (and c205b8a94_base_is_power_of_two
         (< c205b8a94_matched_quote_amount c205b8a94_matched_base_amount))
    (not c205b8a94_zero_cost_trade_revert_occurred)))
(define-fun report_effects () Bool (and c205b8a94_base_is_power_of_two
     (< c205b8a94_matched_quote_amount c205b8a94_matched_base_amount)
     c205b8a94_zero_cost_trade_revert_occurred
     c205b8a94_zero_cost_trade_revert_occurred))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
