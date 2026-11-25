; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce4cc1b7e_dequeue_gas_exhausted_dos () Bool)
(declare-fun ce4cc1b7e_dequeue_processing_completes () Bool)
(declare-fun ce4cc1b7e_queue_loop_bounded () Bool)
(declare-fun ce4cc1b7e_spam_request_share_amount () Int)
(declare-fun ce4cc1b7e_user_can_queue_arbitrary_withdrawals () Bool)
(assert
 (= ce4cc1b7e_dequeue_gas_exhausted_dos ce4cc1b7e_dequeue_gas_exhausted_dos))
(assert
 (= ce4cc1b7e_dequeue_processing_completes ce4cc1b7e_dequeue_processing_completes))
(assert
 (= ce4cc1b7e_queue_loop_bounded ce4cc1b7e_queue_loop_bounded))
(assert
 (= ce4cc1b7e_spam_request_share_amount ce4cc1b7e_spam_request_share_amount))
(assert
 (= ce4cc1b7e_user_can_queue_arbitrary_withdrawals ce4cc1b7e_user_can_queue_arbitrary_withdrawals))
(define-fun report_preconditions () Bool (and ce4cc1b7e_user_can_queue_arbitrary_withdrawals
     (= 1 ce4cc1b7e_spam_request_share_amount)
     ce4cc1b7e_queue_loop_bounded))
(define-fun report_safety () Bool ce4cc1b7e_dequeue_processing_completes)
(define-fun report_effects () Bool (and ce4cc1b7e_queue_loop_bounded
     (not ce4cc1b7e_dequeue_processing_completes)
     ce4cc1b7e_dequeue_gas_exhausted_dos
     ce4cc1b7e_dequeue_gas_exhausted_dos))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
