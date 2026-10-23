; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun min_limit_order_amount_in_base () Int)
(declare-fun lot_size_in_base () Int)
(declare-fun remainder_meets_minimum () Bool)
(declare-fun remainder_aligned_to_lot () Bool)
(declare-fun amendment_completed () Bool)
(assert
 (= min_limit_order_amount_in_base min_limit_order_amount_in_base))
(assert
 (= lot_size_in_base lot_size_in_base))
(assert
 (= remainder_meets_minimum remainder_meets_minimum))
(assert
 (= remainder_aligned_to_lot remainder_aligned_to_lot))
(assert
 (= amendment_completed amendment_completed))
(define-fun report_preconditions () Bool (and (> min_limit_order_amount_in_base lot_size_in_base)
     remainder_meets_minimum
     (not remainder_aligned_to_lot)))
(define-fun report_safety () Bool (=> (and (> min_limit_order_amount_in_base lot_size_in_base)
         remainder_meets_minimum
         (not remainder_aligned_to_lot))
    amendment_completed))
(define-fun report_effects () Bool (and (> min_limit_order_amount_in_base lot_size_in_base)
     remainder_meets_minimum
     (not remainder_aligned_to_lot)
     (not amendment_completed)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
