; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c395a2486_least_competitive_order_removed () Bool)
(declare-fun c395a2486_new_order_introduces_new_limit () Bool)
(declare-fun c395a2486_protocol_invariant_holds () Bool)
(declare-fun c395a2486_side_limit_count_at_max () Bool)
(declare-fun c395a2486_worst_queue_order_count () Int)
(assert
 (= c395a2486_least_competitive_order_removed c395a2486_least_competitive_order_removed))
(assert
 (= c395a2486_new_order_introduces_new_limit c395a2486_new_order_introduces_new_limit))
(assert
 (= c395a2486_protocol_invariant_holds c395a2486_protocol_invariant_holds))
(assert
 (= c395a2486_side_limit_count_at_max c395a2486_side_limit_count_at_max))
(assert
 (= c395a2486_worst_queue_order_count c395a2486_worst_queue_order_count))
(define-fun report_preconditions () Bool (and (< 1 c395a2486_worst_queue_order_count)
     c395a2486_new_order_introduces_new_limit
     c395a2486_side_limit_count_at_max))
(define-fun report_safety () Bool (=> (and c395a2486_side_limit_count_at_max
         c395a2486_new_order_introduces_new_limit)
    (and c395a2486_least_competitive_order_removed
         c395a2486_protocol_invariant_holds)))
(define-fun report_effects () Bool (and c395a2486_side_limit_count_at_max
     c395a2486_new_order_introduces_new_limit
     (not (and c395a2486_least_competitive_order_removed
               c395a2486_protocol_invariant_holds))))
