; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c80326eb2_amounts_disjoint_bits () Bool)
(declare-fun c80326eb2_legitimate_trade_fails_misleading_error () Bool)
(declare-fun c80326eb2_limit_order_matching_in_progress () Bool)
(declare-fun c80326eb2_matched_base_is_power_of_two () Bool)
(declare-fun c80326eb2_matched_quote_less_than_base () Bool)
(assert
 (= c80326eb2_amounts_disjoint_bits c80326eb2_amounts_disjoint_bits))
(assert
 (= c80326eb2_legitimate_trade_fails_misleading_error c80326eb2_legitimate_trade_fails_misleading_error))
(assert
 (= c80326eb2_limit_order_matching_in_progress c80326eb2_limit_order_matching_in_progress))
(assert
 (= c80326eb2_matched_base_is_power_of_two c80326eb2_matched_base_is_power_of_two))
(assert
 (= c80326eb2_matched_quote_less_than_base c80326eb2_matched_quote_less_than_base))
(define-fun report_preconditions () Bool (and c80326eb2_limit_order_matching_in_progress
     c80326eb2_matched_base_is_power_of_two
     c80326eb2_matched_quote_less_than_base
     c80326eb2_amounts_disjoint_bits))
(define-fun report_safety () Bool (=> c80326eb2_legitimate_trade_fails_misleading_error
    (=> (and c80326eb2_limit_order_matching_in_progress
             c80326eb2_matched_base_is_power_of_two
             c80326eb2_matched_quote_less_than_base
             c80326eb2_amounts_disjoint_bits)
        (not c80326eb2_legitimate_trade_fails_misleading_error))))
(define-fun report_effects () Bool (and c80326eb2_legitimate_trade_fails_misleading_error
     c80326eb2_limit_order_matching_in_progress
     c80326eb2_matched_base_is_power_of_two
     c80326eb2_matched_quote_less_than_base
     c80326eb2_amounts_disjoint_bits
     (not (not c80326eb2_legitimate_trade_fails_misleading_error))))
