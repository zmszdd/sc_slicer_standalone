; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun cda2f2085_actual_holder_address () ReportAddress)
(declare-fun cda2f2085_event_from_address () ReportAddress)
(declare-fun cda2f2085_from_holder_is_debited () Bool)
(declare-fun cda2f2085_transfer_from_invoked () Bool)
(assert
 (= cda2f2085_actual_holder_address cda2f2085_actual_holder_address))
(assert
 (= cda2f2085_event_from_address cda2f2085_event_from_address))
(assert
 (= cda2f2085_from_holder_is_debited cda2f2085_from_holder_is_debited))
(assert
 (= cda2f2085_transfer_from_invoked cda2f2085_transfer_from_invoked))
(define-fun report_preconditions () Bool (and cda2f2085_transfer_from_invoked cda2f2085_from_holder_is_debited))
(define-fun report_safety () Bool (=> (and cda2f2085_transfer_from_invoked cda2f2085_from_holder_is_debited)
    (= cda2f2085_event_from_address cda2f2085_actual_holder_address)))
(define-fun report_effects () Bool (and cda2f2085_transfer_from_invoked
     cda2f2085_from_holder_is_debited
     (not (= cda2f2085_event_from_address cda2f2085_actual_holder_address))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
