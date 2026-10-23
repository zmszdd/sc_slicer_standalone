; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7e6b4d3a_deadline_specified () Bool)
(declare-fun c7e6b4d3a_executed_at_unexpected_time () Bool)
(declare-fun c7e6b4d3a_transaction_delayed () Bool)
(assert
 (= c7e6b4d3a_deadline_specified c7e6b4d3a_deadline_specified))
(assert
 (= c7e6b4d3a_executed_at_unexpected_time c7e6b4d3a_executed_at_unexpected_time))
(assert
 (= c7e6b4d3a_transaction_delayed c7e6b4d3a_transaction_delayed))
(define-fun report_preconditions () Bool (and (not c7e6b4d3a_deadline_specified) c7e6b4d3a_transaction_delayed))
(define-fun report_safety () Bool (=> (and (not c7e6b4d3a_deadline_specified) c7e6b4d3a_transaction_delayed)
    (not c7e6b4d3a_executed_at_unexpected_time)))
(define-fun report_effects () Bool (and (not c7e6b4d3a_deadline_specified)
     c7e6b4d3a_transaction_delayed
     (not (not c7e6b4d3a_executed_at_unexpected_time))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
