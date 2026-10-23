; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cf4671d74_max_limits_per_side () Int)
(declare-fun cf4671d74_new_order_introduces_new_limit () Bool)
(declare-fun cf4671d74_side_limit_count_before () Int)
(declare-fun cf4671d74_side_tree_size_after () Int)
(declare-fun cf4671d74_tree_grows_unintended_occurred () Bool)
(declare-fun cf4671d74_worst_queue_order_count () Int)
(assert
 (= cf4671d74_max_limits_per_side cf4671d74_max_limits_per_side))
(assert
 (= cf4671d74_new_order_introduces_new_limit cf4671d74_new_order_introduces_new_limit))
(assert
 (= cf4671d74_side_limit_count_before cf4671d74_side_limit_count_before))
(assert
 (= cf4671d74_side_tree_size_after cf4671d74_side_tree_size_after))
(assert
 (= cf4671d74_tree_grows_unintended_occurred cf4671d74_tree_grows_unintended_occurred))
(assert
 (= cf4671d74_worst_queue_order_count cf4671d74_worst_queue_order_count))
(define-fun report_preconditions () Bool (and (< 1 cf4671d74_worst_queue_order_count)
     cf4671d74_new_order_introduces_new_limit
     (>= cf4671d74_side_limit_count_before cf4671d74_max_limits_per_side)))
(define-fun report_safety () Bool (=> (and (< 1 cf4671d74_worst_queue_order_count)
         cf4671d74_new_order_introduces_new_limit
         (>= cf4671d74_side_limit_count_before cf4671d74_max_limits_per_side))
    (and (<= cf4671d74_side_tree_size_after cf4671d74_max_limits_per_side)
         (not cf4671d74_tree_grows_unintended_occurred))))
(define-fun report_effects () Bool (and (< 1 cf4671d74_worst_queue_order_count)
     cf4671d74_new_order_introduces_new_limit
     (>= cf4671d74_side_limit_count_before cf4671d74_max_limits_per_side)
     (not (and (<= cf4671d74_side_tree_size_after cf4671d74_max_limits_per_side)
               (not cf4671d74_tree_grows_unintended_occurred)))))
