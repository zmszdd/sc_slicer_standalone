; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun c28a7591b_decreased_balance_holder () ReportAddress)
(declare-fun c28a7591b_event_from_field () ReportAddress)
(declare-fun c28a7591b_event_immutable_after_deploy () Bool)
(declare-fun c28a7591b_transfer_from_called () Bool)
(assert
 (= c28a7591b_decreased_balance_holder c28a7591b_decreased_balance_holder))
(assert
 (= c28a7591b_event_from_field c28a7591b_event_from_field))
(assert
 (= c28a7591b_event_immutable_after_deploy c28a7591b_event_immutable_after_deploy))
(assert
 (= c28a7591b_transfer_from_called c28a7591b_transfer_from_called))
(define-fun report_preconditions () Bool c28a7591b_transfer_from_called)
(define-fun report_safety () Bool (=> c28a7591b_event_immutable_after_deploy
    (=> c28a7591b_transfer_from_called
        (= c28a7591b_event_from_field c28a7591b_decreased_balance_holder))))
(define-fun report_effects () Bool (and c28a7591b_event_immutable_after_deploy
     c28a7591b_transfer_from_called
     (not (= c28a7591b_event_from_field c28a7591b_decreased_balance_holder))))
