; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun price_level_has_earlier_orders () Bool)
(declare-fun earlier_orders_reachable_after_removal () Bool)
(assert
 (= price_level_has_earlier_orders price_level_has_earlier_orders))
(assert
 (= earlier_orders_reachable_after_removal earlier_orders_reachable_after_removal))
(define-fun report_preconditions () Bool price_level_has_earlier_orders)
(define-fun report_safety () Bool (=> price_level_has_earlier_orders earlier_orders_reachable_after_removal))
(define-fun report_effects () Bool (and price_level_has_earlier_orders
     (not earlier_orders_reachable_after_removal)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
