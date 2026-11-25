; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9456c820_ask_tree_size () Int)
(declare-fun c9456c820_max_num_limits_per_side () Int)
(declare-fun c9456c820_new_order_introduces_new_limit () Bool)
(declare-fun c9456c820_worst_queue_order_count () Int)
(assert
 (= c9456c820_ask_tree_size c9456c820_ask_tree_size))
(assert
 (= c9456c820_max_num_limits_per_side c9456c820_max_num_limits_per_side))
(assert
 (= c9456c820_new_order_introduces_new_limit c9456c820_new_order_introduces_new_limit))
(assert
 (= c9456c820_worst_queue_order_count c9456c820_worst_queue_order_count))
(define-fun report_preconditions () Bool (and (>= c9456c820_ask_tree_size c9456c820_max_num_limits_per_side)
     (< 1 c9456c820_worst_queue_order_count)
     c9456c820_new_order_introduces_new_limit))
(define-fun report_safety () Bool (=> (>= c9456c820_ask_tree_size c9456c820_max_num_limits_per_side)
    (<= c9456c820_ask_tree_size c9456c820_max_num_limits_per_side)))
(define-fun report_effects () Bool (and (>= c9456c820_ask_tree_size c9456c820_max_num_limits_per_side)
     (not (<= c9456c820_ask_tree_size c9456c820_max_num_limits_per_side))
     (> c9456c820_ask_tree_size c9456c820_max_num_limits_per_side)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
