; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb4d90c6c_base_amount_nonzero () Bool)
(declare-fun cb4d90c6c_limit_order_match_processing () Bool)
(declare-fun cb4d90c6c_matched_amounts_disjoint_bits () Bool)
(declare-fun cb4d90c6c_quote_amount_nonzero () Bool)
(declare-fun cb4d90c6c_zero_cost_trade_revert_occurred () Bool)
(assert
 (= cb4d90c6c_base_amount_nonzero cb4d90c6c_base_amount_nonzero))
(assert
 (= cb4d90c6c_limit_order_match_processing cb4d90c6c_limit_order_match_processing))
(assert
 (= cb4d90c6c_matched_amounts_disjoint_bits cb4d90c6c_matched_amounts_disjoint_bits))
(assert
 (= cb4d90c6c_quote_amount_nonzero cb4d90c6c_quote_amount_nonzero))
(assert
 (= cb4d90c6c_zero_cost_trade_revert_occurred cb4d90c6c_zero_cost_trade_revert_occurred))
(define-fun report_preconditions () Bool (and cb4d90c6c_limit_order_match_processing
     cb4d90c6c_matched_amounts_disjoint_bits))
(define-fun report_safety () Bool (=> cb4d90c6c_zero_cost_trade_revert_occurred
    (=> (and cb4d90c6c_limit_order_match_processing
             cb4d90c6c_base_amount_nonzero
             cb4d90c6c_quote_amount_nonzero)
        (not cb4d90c6c_zero_cost_trade_revert_occurred))))
(define-fun report_effects () Bool (and cb4d90c6c_zero_cost_trade_revert_occurred
     cb4d90c6c_limit_order_match_processing
     cb4d90c6c_base_amount_nonzero
     cb4d90c6c_quote_amount_nonzero
     (not (not cb4d90c6c_zero_cost_trade_revert_occurred))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
