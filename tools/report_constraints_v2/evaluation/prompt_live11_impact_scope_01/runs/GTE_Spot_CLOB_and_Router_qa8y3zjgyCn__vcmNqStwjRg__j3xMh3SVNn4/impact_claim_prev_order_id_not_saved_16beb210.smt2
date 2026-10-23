; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3f0cd5b4_limit_order_added_occurred () Bool)
(declare-fun c3f0cd5b4_order_passed_as_memory_occurred () Bool)
(declare-fun c3f0cd5b4_order_stored_before_limit_update_occurred () Bool)
(declare-fun c3f0cd5b4_prev_order_id_persisted_in_storage () Bool)
(assert
 (= c3f0cd5b4_limit_order_added_occurred c3f0cd5b4_limit_order_added_occurred))
(assert
 (= c3f0cd5b4_order_passed_as_memory_occurred c3f0cd5b4_order_passed_as_memory_occurred))
(assert
 (= c3f0cd5b4_order_stored_before_limit_update_occurred c3f0cd5b4_order_stored_before_limit_update_occurred))
(assert
 (= c3f0cd5b4_prev_order_id_persisted_in_storage c3f0cd5b4_prev_order_id_persisted_in_storage))
(define-fun report_preconditions () Bool (and c3f0cd5b4_limit_order_added_occurred
     c3f0cd5b4_order_stored_before_limit_update_occurred
     c3f0cd5b4_order_passed_as_memory_occurred))
(define-fun report_safety () Bool (=> (and c3f0cd5b4_limit_order_added_occurred
         c3f0cd5b4_order_stored_before_limit_update_occurred
         c3f0cd5b4_order_passed_as_memory_occurred)
    c3f0cd5b4_prev_order_id_persisted_in_storage))
(define-fun report_effects () Bool (and c3f0cd5b4_limit_order_added_occurred
     c3f0cd5b4_order_stored_before_limit_update_occurred
     c3f0cd5b4_order_passed_as_memory_occurred
     (not c3f0cd5b4_prev_order_id_persisted_in_storage)))
