; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c65fd763f_ask_tree_size_at_check () Int)
(declare-fun c65fd763f_least_competitive_order_removed () Bool)
(declare-fun c65fd763f_max_num_limits_per_side () Int)
(declare-fun c65fd763f_new_order_introduces_new_limit () Bool)
(declare-fun c65fd763f_worst_queue_order_count () Int)
(assert
 (= c65fd763f_ask_tree_size_at_check c65fd763f_ask_tree_size_at_check))
(assert
 (= c65fd763f_least_competitive_order_removed c65fd763f_least_competitive_order_removed))
(assert
 (= c65fd763f_max_num_limits_per_side c65fd763f_max_num_limits_per_side))
(assert
 (= c65fd763f_new_order_introduces_new_limit c65fd763f_new_order_introduces_new_limit))
(assert
 (= c65fd763f_worst_queue_order_count c65fd763f_worst_queue_order_count))
(define-fun report_preconditions () Bool (and (>= c65fd763f_ask_tree_size_at_check c65fd763f_max_num_limits_per_side)
     (< 1 c65fd763f_worst_queue_order_count)
     c65fd763f_new_order_introduces_new_limit))
(define-fun report_safety () Bool (=> (and (>= c65fd763f_ask_tree_size_at_check c65fd763f_max_num_limits_per_side)
         (< 1 c65fd763f_worst_queue_order_count)
         c65fd763f_new_order_introduces_new_limit)
    c65fd763f_least_competitive_order_removed))
(define-fun report_effects () Bool (and (>= c65fd763f_ask_tree_size_at_check c65fd763f_max_num_limits_per_side)
     (< 1 c65fd763f_worst_queue_order_count)
     c65fd763f_new_order_introduces_new_limit
     (not c65fd763f_least_competitive_order_removed)
     (not c65fd763f_least_competitive_order_removed)
     c65fd763f_new_order_introduces_new_limit))
