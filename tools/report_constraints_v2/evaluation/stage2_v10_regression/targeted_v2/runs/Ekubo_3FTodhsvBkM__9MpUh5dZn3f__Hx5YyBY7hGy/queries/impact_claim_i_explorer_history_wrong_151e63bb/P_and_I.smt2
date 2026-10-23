; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun c8b006c6f_event_from_address () ReportAddress)
(declare-fun c8b006c6f_explorer_shows_holder_as_origin () Bool)
(declare-fun c8b006c6f_from_holder_is_actual_holder () Bool)
(declare-fun c8b006c6f_holder_address () ReportAddress)
(declare-fun c8b006c6f_transfer_from_invoked () Bool)
(assert
 (= c8b006c6f_event_from_address c8b006c6f_event_from_address))
(assert
 (= c8b006c6f_explorer_shows_holder_as_origin c8b006c6f_explorer_shows_holder_as_origin))
(assert
 (= c8b006c6f_from_holder_is_actual_holder c8b006c6f_from_holder_is_actual_holder))
(assert
 (= c8b006c6f_holder_address c8b006c6f_holder_address))
(assert
 (= c8b006c6f_transfer_from_invoked c8b006c6f_transfer_from_invoked))
(define-fun report_preconditions () Bool (and c8b006c6f_transfer_from_invoked c8b006c6f_from_holder_is_actual_holder))
(define-fun report_safety () Bool (=> (and c8b006c6f_transfer_from_invoked c8b006c6f_from_holder_is_actual_holder)
    (and (= c8b006c6f_event_from_address c8b006c6f_holder_address)
         c8b006c6f_explorer_shows_holder_as_origin)))
(define-fun report_effects () Bool (and c8b006c6f_transfer_from_invoked
     c8b006c6f_from_holder_is_actual_holder
     (not (and (= c8b006c6f_event_from_address c8b006c6f_holder_address)
               c8b006c6f_explorer_shows_holder_as_origin))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
