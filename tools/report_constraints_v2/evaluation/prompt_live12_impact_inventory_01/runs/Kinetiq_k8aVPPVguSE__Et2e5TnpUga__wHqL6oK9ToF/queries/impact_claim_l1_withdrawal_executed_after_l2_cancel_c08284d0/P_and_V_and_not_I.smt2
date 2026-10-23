; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c15a52091_l1_withdrawal_executed_after_cancel () Bool)
(declare-fun c15a52091_manager_cancel_called () Bool)
(declare-fun c15a52091_operator_process_called () Bool)
(declare-fun c15a52091_user_withdrawal_queued () Bool)
(assert
 (= c15a52091_l1_withdrawal_executed_after_cancel c15a52091_l1_withdrawal_executed_after_cancel))
(assert
 (= c15a52091_manager_cancel_called c15a52091_manager_cancel_called))
(assert
 (= c15a52091_operator_process_called c15a52091_operator_process_called))
(assert
 (= c15a52091_user_withdrawal_queued c15a52091_user_withdrawal_queued))
(define-fun report_preconditions () Bool (and c15a52091_user_withdrawal_queued
     c15a52091_manager_cancel_called
     c15a52091_operator_process_called))
(define-fun report_safety () Bool (=> (and c15a52091_user_withdrawal_queued
         c15a52091_manager_cancel_called
         c15a52091_operator_process_called)
    (not c15a52091_l1_withdrawal_executed_after_cancel)))
(define-fun report_effects () Bool (and c15a52091_user_withdrawal_queued
     c15a52091_manager_cancel_called
     c15a52091_operator_process_called
     (not (not c15a52091_l1_withdrawal_executed_after_cancel))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
