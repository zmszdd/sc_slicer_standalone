; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c58ab1976_expiring_orders_supported () Bool)
(declare-fun c58ab1976_fees_only_on_matching () Bool)
(declare-fun c58ab1976_legitimate_post_only_order () Bool)
(declare-fun c58ab1976_order_placement_is_free () Bool)
(declare-fun c58ab1976_post_only_order_blocked () Bool)
(assert
 (= c58ab1976_expiring_orders_supported c58ab1976_expiring_orders_supported))
(assert
 (= c58ab1976_fees_only_on_matching c58ab1976_fees_only_on_matching))
(assert
 (= c58ab1976_legitimate_post_only_order c58ab1976_legitimate_post_only_order))
(assert
 (= c58ab1976_order_placement_is_free c58ab1976_order_placement_is_free))
(assert
 (= c58ab1976_post_only_order_blocked c58ab1976_post_only_order_blocked))
(define-fun report_preconditions () Bool (and c58ab1976_order_placement_is_free
     c58ab1976_fees_only_on_matching
     c58ab1976_expiring_orders_supported))
(define-fun report_safety () Bool (=> c58ab1976_post_only_order_blocked
    (=> (and c58ab1976_order_placement_is_free
             c58ab1976_fees_only_on_matching
             c58ab1976_expiring_orders_supported
             c58ab1976_legitimate_post_only_order)
        (not c58ab1976_post_only_order_blocked))))
(define-fun report_effects () Bool (and c58ab1976_post_only_order_blocked
     c58ab1976_order_placement_is_free
     c58ab1976_fees_only_on_matching
     c58ab1976_expiring_orders_supported
     c58ab1976_legitimate_post_only_order
     (not (not c58ab1976_post_only_order_blocked))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
