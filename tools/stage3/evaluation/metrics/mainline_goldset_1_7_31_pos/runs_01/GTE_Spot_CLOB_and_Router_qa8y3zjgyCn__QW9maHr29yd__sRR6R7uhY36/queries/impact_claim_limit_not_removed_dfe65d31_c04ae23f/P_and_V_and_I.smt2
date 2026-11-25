; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbc34ce45_ask_tree_size_at_max () Int)
(declare-fun cbc34ce45_limit_removed () Bool)
(declare-fun cbc34ce45_max_num_limits_per_side () Int)
(declare-fun cbc34ce45_new_order_introduces_new_limit () Bool)
(declare-fun cbc34ce45_non_competitive_orders_removed () Bool)
(declare-fun cbc34ce45_worst_queue_order_count () Int)
(assert
 (= cbc34ce45_ask_tree_size_at_max cbc34ce45_ask_tree_size_at_max))
(assert
 (= cbc34ce45_limit_removed cbc34ce45_limit_removed))
(assert
 (= cbc34ce45_max_num_limits_per_side cbc34ce45_max_num_limits_per_side))
(assert
 (= cbc34ce45_new_order_introduces_new_limit cbc34ce45_new_order_introduces_new_limit))
(assert
 (= cbc34ce45_non_competitive_orders_removed cbc34ce45_non_competitive_orders_removed))
(assert
 (= cbc34ce45_worst_queue_order_count cbc34ce45_worst_queue_order_count))
(define-fun report_preconditions () Bool (and (>= cbc34ce45_ask_tree_size_at_max cbc34ce45_max_num_limits_per_side)
     (< 1 cbc34ce45_worst_queue_order_count)
     cbc34ce45_new_order_introduces_new_limit))
(define-fun report_safety () Bool (=> (and (>= cbc34ce45_ask_tree_size_at_max cbc34ce45_max_num_limits_per_side)
         cbc34ce45_new_order_introduces_new_limit)
    cbc34ce45_non_competitive_orders_removed))
(define-fun report_effects () Bool (and (>= cbc34ce45_ask_tree_size_at_max cbc34ce45_max_num_limits_per_side)
     cbc34ce45_new_order_introduces_new_limit
     (not cbc34ce45_non_competitive_orders_removed)
     (not cbc34ce45_limit_removed)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
