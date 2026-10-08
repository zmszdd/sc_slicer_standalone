; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun order_filled () Bool)
(declare-fun base_amount_nonzero () Bool)
(declare-fun quote_amount_nonzero () Bool)
(declare-fun amounts_no_overlapping_bits () Bool)
(declare-fun zero_cost_trade_revert () Bool)
(assert
 (= order_filled order_filled))
(assert
 (= base_amount_nonzero base_amount_nonzero))
(assert
 (= quote_amount_nonzero quote_amount_nonzero))
(assert
 (= amounts_no_overlapping_bits amounts_no_overlapping_bits))
(assert
 (= zero_cost_trade_revert zero_cost_trade_revert))
(define-fun report_preconditions () Bool (and order_filled
     base_amount_nonzero
     quote_amount_nonzero
     amounts_no_overlapping_bits))
(define-fun report_safety () Bool (=> (and order_filled
         base_amount_nonzero
         quote_amount_nonzero
         amounts_no_overlapping_bits)
    (not zero_cost_trade_revert)))
(define-fun report_effects () Bool (and order_filled
     base_amount_nonzero
     quote_amount_nonzero
     amounts_no_overlapping_bits
     (not (not zero_cost_trade_revert))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
