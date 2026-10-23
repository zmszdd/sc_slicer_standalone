; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc581f1c6_max_num_limits_per_side () Int)
(declare-fun cc581f1c6_new_limit_introduced () Bool)
(declare-fun cc581f1c6_non_competitive_orders_retained () Bool)
(declare-fun cc581f1c6_side_tree_size_after () Int)
(declare-fun cc581f1c6_worst_queue_order_count () Int)
(assert
 (= cc581f1c6_max_num_limits_per_side cc581f1c6_max_num_limits_per_side))
(assert
 (= cc581f1c6_new_limit_introduced cc581f1c6_new_limit_introduced))
(assert
 (= cc581f1c6_non_competitive_orders_retained cc581f1c6_non_competitive_orders_retained))
(assert
 (= cc581f1c6_side_tree_size_after cc581f1c6_side_tree_size_after))
(assert
 (= cc581f1c6_worst_queue_order_count cc581f1c6_worst_queue_order_count))
(define-fun report_preconditions () Bool (and (< 1 cc581f1c6_worst_queue_order_count) cc581f1c6_new_limit_introduced))
(define-fun report_safety () Bool (=> (and (>= cc581f1c6_side_tree_size_after cc581f1c6_max_num_limits_per_side)
         cc581f1c6_new_limit_introduced)
    (and (<= cc581f1c6_side_tree_size_after cc581f1c6_max_num_limits_per_side)
         (not cc581f1c6_non_competitive_orders_retained))))
(define-fun report_effects () Bool (and (>= cc581f1c6_side_tree_size_after cc581f1c6_max_num_limits_per_side)
     cc581f1c6_new_limit_introduced
     (not (and (<= cc581f1c6_side_tree_size_after
                   cc581f1c6_max_num_limits_per_side)
               (not cc581f1c6_non_competitive_orders_retained)))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
