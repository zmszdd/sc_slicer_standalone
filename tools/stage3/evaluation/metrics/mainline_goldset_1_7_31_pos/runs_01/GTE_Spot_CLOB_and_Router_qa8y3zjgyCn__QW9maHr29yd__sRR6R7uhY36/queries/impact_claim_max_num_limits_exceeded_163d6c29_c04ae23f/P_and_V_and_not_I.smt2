; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb0da716a_ask_tree_size () Int)
(declare-fun cb0da716a_ask_tree_size_after_add () Int)
(declare-fun cb0da716a_max_num_limits_per_side () Int)
(declare-fun cb0da716a_new_order_introduces_new_limit () Bool)
(declare-fun cb0da716a_worst_queue_order_count () Int)
(assert
 (= cb0da716a_ask_tree_size cb0da716a_ask_tree_size))
(assert
 (= cb0da716a_ask_tree_size_after_add cb0da716a_ask_tree_size_after_add))
(assert
 (= cb0da716a_max_num_limits_per_side cb0da716a_max_num_limits_per_side))
(assert
 (= cb0da716a_new_order_introduces_new_limit cb0da716a_new_order_introduces_new_limit))
(assert
 (= cb0da716a_worst_queue_order_count cb0da716a_worst_queue_order_count))
(define-fun report_preconditions () Bool (and (>= cb0da716a_ask_tree_size cb0da716a_max_num_limits_per_side)
     (< 1 cb0da716a_worst_queue_order_count)
     cb0da716a_new_order_introduces_new_limit))
(define-fun report_safety () Bool (=> cb0da716a_new_order_introduces_new_limit
    (<= cb0da716a_ask_tree_size_after_add cb0da716a_max_num_limits_per_side)))
(define-fun report_effects () Bool (and cb0da716a_new_order_introduces_new_limit
     (not (<= cb0da716a_ask_tree_size_after_add
              cb0da716a_max_num_limits_per_side))
     (> cb0da716a_ask_tree_size_after_add cb0da716a_max_num_limits_per_side)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
