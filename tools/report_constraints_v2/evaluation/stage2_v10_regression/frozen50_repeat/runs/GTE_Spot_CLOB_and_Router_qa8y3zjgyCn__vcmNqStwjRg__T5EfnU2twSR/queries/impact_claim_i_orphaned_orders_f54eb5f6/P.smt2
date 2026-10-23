; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca8e7df36_counters_reflect_reachable_only () Bool)
(declare-fun ca8e7df36_new_order_appended () Bool)
(declare-fun ca8e7df36_non_head_order_exists () Bool)
(declare-fun ca8e7df36_order_reachable_via_chain () Bool)
(assert
 (= ca8e7df36_counters_reflect_reachable_only ca8e7df36_counters_reflect_reachable_only))
(assert
 (= ca8e7df36_new_order_appended ca8e7df36_new_order_appended))
(assert
 (= ca8e7df36_non_head_order_exists ca8e7df36_non_head_order_exists))
(assert
 (= ca8e7df36_order_reachable_via_chain ca8e7df36_order_reachable_via_chain))
(define-fun report_preconditions () Bool (and ca8e7df36_non_head_order_exists ca8e7df36_new_order_appended))
(define-fun report_safety () Bool (=> (and ca8e7df36_non_head_order_exists ca8e7df36_new_order_appended)
    (and ca8e7df36_order_reachable_via_chain
         ca8e7df36_counters_reflect_reachable_only)))
(define-fun report_effects () Bool (and ca8e7df36_non_head_order_exists
     ca8e7df36_new_order_appended
     (not (and ca8e7df36_order_reachable_via_chain
               ca8e7df36_counters_reflect_reachable_only))))
(assert report_preconditions)
(check-sat)
(get-model)
