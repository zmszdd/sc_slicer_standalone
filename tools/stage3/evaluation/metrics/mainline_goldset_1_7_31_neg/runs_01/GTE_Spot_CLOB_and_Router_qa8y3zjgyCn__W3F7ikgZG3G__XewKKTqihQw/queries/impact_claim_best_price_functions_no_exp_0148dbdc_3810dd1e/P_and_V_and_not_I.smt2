; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6b7b9b41_price_level_with_no_live_orders_remains_in_tree () Bool)
(declare-fun c6b7b9b41_returned_price_from_expired_orders () Bool)
(assert
 (= c6b7b9b41_price_level_with_no_live_orders_remains_in_tree c6b7b9b41_price_level_with_no_live_orders_remains_in_tree))
(assert
 (= c6b7b9b41_returned_price_from_expired_orders c6b7b9b41_returned_price_from_expired_orders))
(define-fun report_preconditions () Bool (and true c6b7b9b41_price_level_with_no_live_orders_remains_in_tree))
(define-fun report_safety () Bool (not c6b7b9b41_returned_price_from_expired_orders))
(define-fun report_effects () Bool (and c6b7b9b41_price_level_with_no_live_orders_remains_in_tree
     c6b7b9b41_returned_price_from_expired_orders
     c6b7b9b41_returned_price_from_expired_orders))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
