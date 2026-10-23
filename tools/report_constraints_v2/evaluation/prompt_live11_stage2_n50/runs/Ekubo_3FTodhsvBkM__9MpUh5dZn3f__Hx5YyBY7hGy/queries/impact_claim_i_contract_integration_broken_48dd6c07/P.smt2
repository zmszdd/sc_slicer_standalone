; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
 (declare-fun c50ec6c57_event_from_address () ReportAddress)
(declare-fun c50ec6c57_from_is_holder () Bool)
(declare-fun c50ec6c57_holder_address () ReportAddress)
(declare-fun c50ec6c57_integration_broken () Bool)
(declare-fun c50ec6c57_transfer_from_invoked () Bool)
(assert
 (= c50ec6c57_event_from_address c50ec6c57_event_from_address))
(assert
 (= c50ec6c57_from_is_holder c50ec6c57_from_is_holder))
(assert
 (= c50ec6c57_holder_address c50ec6c57_holder_address))
(assert
 (= c50ec6c57_integration_broken c50ec6c57_integration_broken))
(assert
 (= c50ec6c57_transfer_from_invoked c50ec6c57_transfer_from_invoked))
(define-fun report_preconditions () Bool (and c50ec6c57_transfer_from_invoked c50ec6c57_from_is_holder))
(define-fun report_safety () Bool (=> (and c50ec6c57_transfer_from_invoked c50ec6c57_from_is_holder)
    (and (= c50ec6c57_event_from_address c50ec6c57_holder_address)
         (not c50ec6c57_integration_broken))))
(define-fun report_effects () Bool (and c50ec6c57_transfer_from_invoked
     c50ec6c57_from_is_holder
     (not (and (= c50ec6c57_event_from_address c50ec6c57_holder_address)
               (not c50ec6c57_integration_broken)))))
(assert report_preconditions)
(check-sat)
(get-model)
