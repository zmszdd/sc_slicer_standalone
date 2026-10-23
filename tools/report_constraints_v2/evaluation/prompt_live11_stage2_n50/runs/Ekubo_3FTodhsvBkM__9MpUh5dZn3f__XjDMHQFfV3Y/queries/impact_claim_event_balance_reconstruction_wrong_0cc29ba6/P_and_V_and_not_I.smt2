; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
 (declare-fun ccb79c80c_caller_is_holder () Bool)
(declare-fun ccb79c80c_debited_holder_address () ReportAddress)
(declare-fun ccb79c80c_event_balance_reconstruction_correct () Bool)
(declare-fun ccb79c80c_event_from_address () ReportAddress)
(assert
 (= ccb79c80c_caller_is_holder ccb79c80c_caller_is_holder))
(assert
 (= ccb79c80c_debited_holder_address ccb79c80c_debited_holder_address))
(assert
 (= ccb79c80c_event_balance_reconstruction_correct ccb79c80c_event_balance_reconstruction_correct))
(assert
 (= ccb79c80c_event_from_address ccb79c80c_event_from_address))
(define-fun report_preconditions () Bool (not ccb79c80c_caller_is_holder))
(define-fun report_safety () Bool (=> (not ccb79c80c_caller_is_holder)
    (and (= ccb79c80c_event_from_address ccb79c80c_debited_holder_address)
         ccb79c80c_event_balance_reconstruction_correct)))
(define-fun report_effects () Bool (and (not ccb79c80c_caller_is_holder)
     (not (and (= ccb79c80c_event_from_address ccb79c80c_debited_holder_address)
               ccb79c80c_event_balance_reconstruction_correct))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
