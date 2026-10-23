; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun c77f55940_caller_is_not_holder () Bool)
(declare-fun c77f55940_debited_holder_address () ReportAddress)
(declare-fun c77f55940_event_from_address () ReportAddress)
(declare-fun c77f55940_event_reconstructed_balances_correct () Bool)
(assert
 (= c77f55940_caller_is_not_holder c77f55940_caller_is_not_holder))
(assert
 (= c77f55940_debited_holder_address c77f55940_debited_holder_address))
(assert
 (= c77f55940_event_from_address c77f55940_event_from_address))
(assert
 (= c77f55940_event_reconstructed_balances_correct c77f55940_event_reconstructed_balances_correct))
(define-fun report_preconditions () Bool c77f55940_caller_is_not_holder)
(define-fun report_safety () Bool (=> c77f55940_caller_is_not_holder
    (and (= c77f55940_event_from_address c77f55940_debited_holder_address)
         c77f55940_event_reconstructed_balances_correct)))
(define-fun report_effects () Bool (and c77f55940_caller_is_not_holder
     (not (and (= c77f55940_event_from_address c77f55940_debited_holder_address)
               c77f55940_event_reconstructed_balances_correct))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
