; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun c90dbc5d4_caller_is_not_holder () Bool)
(declare-fun c90dbc5d4_debited_holder_address () ReportAddress)
(declare-fun c90dbc5d4_event_from_address () ReportAddress)
(assert
 (= c90dbc5d4_caller_is_not_holder c90dbc5d4_caller_is_not_holder))
(assert
 (= c90dbc5d4_debited_holder_address c90dbc5d4_debited_holder_address))
(assert
 (= c90dbc5d4_event_from_address c90dbc5d4_event_from_address))
(define-fun report_preconditions () Bool c90dbc5d4_caller_is_not_holder)
(define-fun report_safety () Bool (=> c90dbc5d4_caller_is_not_holder
    (= c90dbc5d4_event_from_address c90dbc5d4_debited_holder_address)))
(define-fun report_effects () Bool (and c90dbc5d4_caller_is_not_holder
     (not (= c90dbc5d4_event_from_address c90dbc5d4_debited_holder_address))))
(assert report_preconditions)
(check-sat)
(get-model)
