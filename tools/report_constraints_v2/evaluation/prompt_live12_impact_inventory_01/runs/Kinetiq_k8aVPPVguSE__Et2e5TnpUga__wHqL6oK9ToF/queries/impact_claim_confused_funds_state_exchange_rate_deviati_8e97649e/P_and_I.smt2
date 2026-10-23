; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cfae0ce53_exchange_rate_matches_reality () Bool)
(declare-fun cfae0ce53_manager_cancel_invoked () Bool)
(declare-fun cfae0ce53_operator_processes_queue () Bool)
(declare-fun cfae0ce53_user_withdrawal_queued () Bool)
(assert
 (= cfae0ce53_exchange_rate_matches_reality cfae0ce53_exchange_rate_matches_reality))
(assert
 (= cfae0ce53_manager_cancel_invoked cfae0ce53_manager_cancel_invoked))
(assert
 (= cfae0ce53_operator_processes_queue cfae0ce53_operator_processes_queue))
(assert
 (= cfae0ce53_user_withdrawal_queued cfae0ce53_user_withdrawal_queued))
(define-fun report_preconditions () Bool (and cfae0ce53_user_withdrawal_queued
     cfae0ce53_manager_cancel_invoked
     cfae0ce53_operator_processes_queue))
(define-fun report_safety () Bool (=> cfae0ce53_operator_processes_queue cfae0ce53_exchange_rate_matches_reality))
(define-fun report_effects () Bool (and cfae0ce53_operator_processes_queue
     (not cfae0ce53_exchange_rate_matches_reality)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
