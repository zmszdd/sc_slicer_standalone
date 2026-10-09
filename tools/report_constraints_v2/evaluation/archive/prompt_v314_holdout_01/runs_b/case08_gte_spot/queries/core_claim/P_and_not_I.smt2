; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun order_in_memory_only () Bool)
(declare-fun prev_order_id_zero () Bool)
(declare-fun middle_order_prev_link_broken () Bool)
(declare-fun middle_order_removed_flag () Bool)
(declare-fun head_order_lost () Bool)
(assert
 (= order_in_memory_only order_in_memory_only))
(assert
 (= prev_order_id_zero prev_order_id_zero))
(assert
 (= middle_order_prev_link_broken middle_order_prev_link_broken))
(assert
 (= middle_order_removed_flag middle_order_removed_flag))
(assert
 (= head_order_lost head_order_lost))
(define-fun report_preconditions () Bool (and order_in_memory_only
     order_in_memory_only
     prev_order_id_zero
     middle_order_prev_link_broken
     middle_order_removed_flag))
(define-fun report_safety () Bool (=> middle_order_removed_flag (not head_order_lost)))
(define-fun report_effects () Bool (and middle_order_removed_flag head_order_lost))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
