; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
 (declare-fun cb2af3cd6_event_from_address () ReportAddress)
(declare-fun cb2af3cd6_from_is_holder () Bool)
(declare-fun cb2af3cd6_holder_address () ReportAddress)
(declare-fun cb2af3cd6_transfer_from_invoked () Bool)
(assert
 (= cb2af3cd6_event_from_address cb2af3cd6_event_from_address))
(assert
 (= cb2af3cd6_from_is_holder cb2af3cd6_from_is_holder))
(assert
 (= cb2af3cd6_holder_address cb2af3cd6_holder_address))
(assert
 (= cb2af3cd6_transfer_from_invoked cb2af3cd6_transfer_from_invoked))
(define-fun report_preconditions () Bool (and cb2af3cd6_transfer_from_invoked cb2af3cd6_from_is_holder))
(define-fun report_safety () Bool (=> (and cb2af3cd6_transfer_from_invoked cb2af3cd6_from_is_holder)
    (= cb2af3cd6_event_from_address cb2af3cd6_holder_address)))
(define-fun report_effects () Bool (and cb2af3cd6_transfer_from_invoked
     cb2af3cd6_from_is_holder
     (not (= cb2af3cd6_event_from_address cb2af3cd6_holder_address))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
