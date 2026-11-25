; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbe270225_divergence_cap_after_reduction () Int)
(declare-fun cbe270225_existing_order_price () Int)
(declare-fun cbe270225_order_price_after_cap_change () Int)
(declare-fun cbe270225_out_of_range_order_closed () Bool)
(assert
 (= cbe270225_divergence_cap_after_reduction cbe270225_divergence_cap_after_reduction))
(assert
 (= cbe270225_existing_order_price cbe270225_existing_order_price))
(assert
 (= cbe270225_order_price_after_cap_change cbe270225_order_price_after_cap_change))
(assert
 (= cbe270225_out_of_range_order_closed cbe270225_out_of_range_order_closed))
(define-fun report_preconditions () Bool (and (< cbe270225_divergence_cap_after_reduction cbe270225_existing_order_price)
     cbe270225_out_of_range_order_closed))
(define-fun report_safety () Bool (<= cbe270225_order_price_after_cap_change
    cbe270225_divergence_cap_after_reduction))
(define-fun report_effects () Bool (and cbe270225_out_of_range_order_closed
     (not (<= cbe270225_order_price_after_cap_change
              cbe270225_divergence_cap_after_reduction))
     (> cbe270225_order_price_after_cap_change
        cbe270225_divergence_cap_after_reduction)
     (< cbe270225_divergence_cap_after_reduction cbe270225_existing_order_price)))
(assert report_preconditions)
(check-sat)
(get-model)
