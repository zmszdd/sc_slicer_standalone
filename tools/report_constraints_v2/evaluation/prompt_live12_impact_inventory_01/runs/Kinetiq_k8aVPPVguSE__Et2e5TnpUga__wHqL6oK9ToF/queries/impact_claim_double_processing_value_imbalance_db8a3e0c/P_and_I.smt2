; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c015d0a13_cancelled_withdrawal_processed_twice () Bool)
(declare-fun c015d0a13_manager_cancel_called () Bool)
(declare-fun c015d0a13_operator_process_called () Bool)
(declare-fun c015d0a13_user_withdrawal_queued () Bool)
(assert
 (= c015d0a13_cancelled_withdrawal_processed_twice c015d0a13_cancelled_withdrawal_processed_twice))
(assert
 (= c015d0a13_manager_cancel_called c015d0a13_manager_cancel_called))
(assert
 (= c015d0a13_operator_process_called c015d0a13_operator_process_called))
(assert
 (= c015d0a13_user_withdrawal_queued c015d0a13_user_withdrawal_queued))
(define-fun report_preconditions () Bool (and c015d0a13_user_withdrawal_queued
     c015d0a13_manager_cancel_called
     c015d0a13_operator_process_called))
(define-fun report_safety () Bool (=> (and c015d0a13_user_withdrawal_queued
         c015d0a13_manager_cancel_called
         c015d0a13_operator_process_called)
    (not c015d0a13_cancelled_withdrawal_processed_twice)))
(define-fun report_effects () Bool (and c015d0a13_user_withdrawal_queued
     c015d0a13_manager_cancel_called
     c015d0a13_operator_process_called
     (not (not c015d0a13_cancelled_withdrawal_processed_twice))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
