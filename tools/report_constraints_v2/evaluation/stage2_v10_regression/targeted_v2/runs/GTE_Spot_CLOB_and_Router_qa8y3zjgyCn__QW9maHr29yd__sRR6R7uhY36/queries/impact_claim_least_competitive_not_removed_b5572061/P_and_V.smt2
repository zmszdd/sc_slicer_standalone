; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8e83812d_least_competitive_removed () Bool)
(declare-fun c8e83812d_max_limits_reached () Bool)
(declare-fun c8e83812d_new_order_new_limit () Bool)
(declare-fun c8e83812d_worst_queue_multiple_orders () Bool)
(assert
 (= c8e83812d_least_competitive_removed c8e83812d_least_competitive_removed))
(assert
 (= c8e83812d_max_limits_reached c8e83812d_max_limits_reached))
(assert
 (= c8e83812d_new_order_new_limit c8e83812d_new_order_new_limit))
(assert
 (= c8e83812d_worst_queue_multiple_orders c8e83812d_worst_queue_multiple_orders))
(define-fun report_preconditions () Bool (and c8e83812d_max_limits_reached
     c8e83812d_worst_queue_multiple_orders
     c8e83812d_new_order_new_limit))
(define-fun report_safety () Bool (=> (and c8e83812d_max_limits_reached c8e83812d_new_order_new_limit)
    c8e83812d_least_competitive_removed))
(define-fun report_effects () Bool (and c8e83812d_max_limits_reached
     c8e83812d_new_order_new_limit
     (not c8e83812d_least_competitive_removed)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
