; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4f3beb33_least_competitive_removed () Bool)
(declare-fun c4f3beb33_max_limits_reached () Bool)
(declare-fun c4f3beb33_new_order_new_limit () Bool)
(declare-fun c4f3beb33_tree_grows_beyond_intended () Bool)
(declare-fun c4f3beb33_worst_queue_multiple_orders () Bool)
(assert
 (= c4f3beb33_least_competitive_removed c4f3beb33_least_competitive_removed))
(assert
 (= c4f3beb33_max_limits_reached c4f3beb33_max_limits_reached))
(assert
 (= c4f3beb33_new_order_new_limit c4f3beb33_new_order_new_limit))
(assert
 (= c4f3beb33_tree_grows_beyond_intended c4f3beb33_tree_grows_beyond_intended))
(assert
 (= c4f3beb33_worst_queue_multiple_orders c4f3beb33_worst_queue_multiple_orders))
(define-fun report_preconditions () Bool (and c4f3beb33_max_limits_reached
     c4f3beb33_worst_queue_multiple_orders
     c4f3beb33_new_order_new_limit))
(define-fun report_safety () Bool (=> (and c4f3beb33_max_limits_reached c4f3beb33_new_order_new_limit)
    (and c4f3beb33_least_competitive_removed
         (not c4f3beb33_tree_grows_beyond_intended))))
(define-fun report_effects () Bool (and c4f3beb33_max_limits_reached
     c4f3beb33_new_order_new_limit
     (not (and c4f3beb33_least_competitive_removed
               (not c4f3beb33_tree_grows_beyond_intended)))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
