; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cf6828692_admin_processing_reverts_out_of_gas () Bool)
(declare-fun cf6828692_loop_bounded_by_request_count () Bool)
(declare-fun cf6828692_spam_request_share_amount () Int)
(declare-fun cf6828692_user_can_queue_arbitrary_withdrawals_occurred () Bool)
(assert
 (= cf6828692_admin_processing_reverts_out_of_gas cf6828692_admin_processing_reverts_out_of_gas))
(assert
 (= cf6828692_loop_bounded_by_request_count cf6828692_loop_bounded_by_request_count))
(assert
 (= cf6828692_spam_request_share_amount cf6828692_spam_request_share_amount))
(assert
 (= cf6828692_user_can_queue_arbitrary_withdrawals_occurred cf6828692_user_can_queue_arbitrary_withdrawals_occurred))
(define-fun report_preconditions () Bool (and cf6828692_user_can_queue_arbitrary_withdrawals_occurred
     (= 1 cf6828692_spam_request_share_amount)
     cf6828692_loop_bounded_by_request_count))
(define-fun report_safety () Bool (not cf6828692_admin_processing_reverts_out_of_gas))
(define-fun report_effects () Bool (and cf6828692_loop_bounded_by_request_count
     cf6828692_admin_processing_reverts_out_of_gas
     cf6828692_admin_processing_reverts_out_of_gas))
