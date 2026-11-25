; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c57a48a5e_ask_tree_size_at_max () Int)
(declare-fun c57a48a5e_least_competitive_order_removed () Bool)
(declare-fun c57a48a5e_max_num_limits_per_side () Int)
(declare-fun c57a48a5e_new_order_introduces_new_limit () Bool)
(declare-fun c57a48a5e_non_competitive_orders_removed () Bool)
(declare-fun c57a48a5e_worst_queue_order_count () Int)
(assert
 (= c57a48a5e_ask_tree_size_at_max c57a48a5e_ask_tree_size_at_max))
(assert
 (= c57a48a5e_least_competitive_order_removed c57a48a5e_least_competitive_order_removed))
(assert
 (= c57a48a5e_max_num_limits_per_side c57a48a5e_max_num_limits_per_side))
(assert
 (= c57a48a5e_new_order_introduces_new_limit c57a48a5e_new_order_introduces_new_limit))
(assert
 (= c57a48a5e_non_competitive_orders_removed c57a48a5e_non_competitive_orders_removed))
(assert
 (= c57a48a5e_worst_queue_order_count c57a48a5e_worst_queue_order_count))
(define-fun report_preconditions () Bool (and (>= c57a48a5e_ask_tree_size_at_max c57a48a5e_max_num_limits_per_side)
     (< 1 c57a48a5e_worst_queue_order_count)
     c57a48a5e_new_order_introduces_new_limit))
(define-fun report_safety () Bool (=> (and (>= c57a48a5e_ask_tree_size_at_max c57a48a5e_max_num_limits_per_side)
         c57a48a5e_new_order_introduces_new_limit)
    c57a48a5e_non_competitive_orders_removed))
(define-fun report_effects () Bool (and (>= c57a48a5e_ask_tree_size_at_max c57a48a5e_max_num_limits_per_side)
     c57a48a5e_new_order_introduces_new_limit
     (not c57a48a5e_non_competitive_orders_removed)
     (not c57a48a5e_least_competitive_order_removed)
     (not c57a48a5e_least_competitive_order_removed)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
