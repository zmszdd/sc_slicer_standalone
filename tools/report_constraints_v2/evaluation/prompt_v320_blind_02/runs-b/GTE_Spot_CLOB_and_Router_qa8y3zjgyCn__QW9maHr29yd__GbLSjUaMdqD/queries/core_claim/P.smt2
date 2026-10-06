; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun max_num_limits_per_side () Int)
(declare-fun tree_size () Int)
(declare-fun worst_level_order_count () Int)
(assert
 (= max_num_limits_per_side max_num_limits_per_side))
(assert
 (= tree_size tree_size))
(assert
 (= worst_level_order_count worst_level_order_count))
(define-fun report_preconditions () Bool (and (= tree_size max_num_limits_per_side) (< 1 worst_level_order_count)))
(define-fun report_safety () Bool (=> (and (= tree_size max_num_limits_per_side) (< 1 worst_level_order_count))
    (<= tree_size max_num_limits_per_side)))
(define-fun report_effects () Bool (and (= tree_size max_num_limits_per_side)
     (< 1 worst_level_order_count)
     (not (<= tree_size max_num_limits_per_side))))
(assert report_preconditions)
(check-sat)
(get-model)
