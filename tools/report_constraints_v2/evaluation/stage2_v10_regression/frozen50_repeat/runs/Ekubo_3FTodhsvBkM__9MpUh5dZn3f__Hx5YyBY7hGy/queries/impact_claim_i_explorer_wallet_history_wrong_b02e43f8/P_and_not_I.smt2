; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun ccacb0278_event_from_address () ReportAddress)
(declare-fun ccacb0278_explorer_shows_operator_as_sender () Bool)
(declare-fun ccacb0278_holder_address () ReportAddress)
(declare-fun ccacb0278_transfer_from_invoked () Bool)
(assert
 (= ccacb0278_event_from_address ccacb0278_event_from_address))
(assert
 (= ccacb0278_explorer_shows_operator_as_sender ccacb0278_explorer_shows_operator_as_sender))
(assert
 (= ccacb0278_holder_address ccacb0278_holder_address))
(assert
 (= ccacb0278_transfer_from_invoked ccacb0278_transfer_from_invoked))
(define-fun report_preconditions () Bool (and ccacb0278_transfer_from_invoked
     (= ccacb0278_event_from_address ccacb0278_holder_address)))
(define-fun report_safety () Bool (=> ccacb0278_transfer_from_invoked
    (and (= ccacb0278_event_from_address ccacb0278_holder_address)
         (not ccacb0278_explorer_shows_operator_as_sender))))
(define-fun report_effects () Bool (and ccacb0278_transfer_from_invoked
     (not (and (= ccacb0278_event_from_address ccacb0278_holder_address)
               (not ccacb0278_explorer_shows_operator_as_sender)))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
