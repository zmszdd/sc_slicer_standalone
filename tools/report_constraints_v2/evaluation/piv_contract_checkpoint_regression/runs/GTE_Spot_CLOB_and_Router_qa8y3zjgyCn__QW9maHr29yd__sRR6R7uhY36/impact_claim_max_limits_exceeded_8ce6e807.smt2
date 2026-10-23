; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0ff6df31_limits_per_side_after_add () Int)
(declare-fun c0ff6df31_max_num_limits_per_side () Int)
(declare-fun c0ff6df31_new_order_introduces_new_limit () Bool)
(declare-fun c0ff6df31_worst_queue_order_count () Int)
(assert
 (= c0ff6df31_limits_per_side_after_add c0ff6df31_limits_per_side_after_add))
(assert
 (= c0ff6df31_max_num_limits_per_side c0ff6df31_max_num_limits_per_side))
(assert
 (= c0ff6df31_new_order_introduces_new_limit c0ff6df31_new_order_introduces_new_limit))
(assert
 (= c0ff6df31_worst_queue_order_count c0ff6df31_worst_queue_order_count))
(define-fun report_preconditions () Bool (and (< 1 c0ff6df31_worst_queue_order_count)
     c0ff6df31_new_order_introduces_new_limit))
(define-fun report_safety () Bool (=> c0ff6df31_new_order_introduces_new_limit
    (<= c0ff6df31_limits_per_side_after_add c0ff6df31_max_num_limits_per_side)))
(define-fun report_effects () Bool (and c0ff6df31_new_order_introduces_new_limit
     (not (<= c0ff6df31_limits_per_side_after_add
              c0ff6df31_max_num_limits_per_side))))
