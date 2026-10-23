; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0ff6df31_max_limits_per_side () Int)
(declare-fun c0ff6df31_new_limit_introduced () Bool)
(declare-fun c0ff6df31_side_limit_count_after () Int)
(declare-fun c0ff6df31_side_limit_count_before () Int)
(declare-fun c0ff6df31_worst_queue_order_count () Int)
(assert
 (= c0ff6df31_max_limits_per_side c0ff6df31_max_limits_per_side))
(assert
 (= c0ff6df31_new_limit_introduced c0ff6df31_new_limit_introduced))
(assert
 (= c0ff6df31_side_limit_count_after c0ff6df31_side_limit_count_after))
(assert
 (= c0ff6df31_side_limit_count_before c0ff6df31_side_limit_count_before))
(assert
 (= c0ff6df31_worst_queue_order_count c0ff6df31_worst_queue_order_count))
(define-fun report_preconditions () Bool (and (< 1 c0ff6df31_worst_queue_order_count) c0ff6df31_new_limit_introduced))
(define-fun report_safety () Bool (=> (and (>= c0ff6df31_side_limit_count_before c0ff6df31_max_limits_per_side)
         c0ff6df31_new_limit_introduced)
    (<= c0ff6df31_side_limit_count_after c0ff6df31_max_limits_per_side)))
(define-fun report_effects () Bool (and (>= c0ff6df31_side_limit_count_before c0ff6df31_max_limits_per_side)
     c0ff6df31_new_limit_introduced
     (not (<= c0ff6df31_side_limit_count_after c0ff6df31_max_limits_per_side))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
