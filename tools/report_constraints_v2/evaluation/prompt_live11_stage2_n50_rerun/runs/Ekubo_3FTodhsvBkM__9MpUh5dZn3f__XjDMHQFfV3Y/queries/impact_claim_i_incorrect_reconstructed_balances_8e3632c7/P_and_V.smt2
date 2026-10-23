; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun c17046646_caller_is_not_holder () Bool)
(declare-fun c17046646_debited_holder_address () ReportAddress)
(declare-fun c17046646_event_from_address () ReportAddress)
(declare-fun c17046646_reconstructed_balances_correct () Bool)
(assert
 (= c17046646_caller_is_not_holder c17046646_caller_is_not_holder))
(assert
 (= c17046646_debited_holder_address c17046646_debited_holder_address))
(assert
 (= c17046646_event_from_address c17046646_event_from_address))
(assert
 (= c17046646_reconstructed_balances_correct c17046646_reconstructed_balances_correct))
(define-fun report_preconditions () Bool c17046646_caller_is_not_holder)
(define-fun report_safety () Bool (=> c17046646_caller_is_not_holder
    (and (= c17046646_event_from_address c17046646_debited_holder_address)
         c17046646_reconstructed_balances_correct)))
(define-fun report_effects () Bool (and c17046646_caller_is_not_holder
     (not (and (= c17046646_event_from_address c17046646_debited_holder_address)
               c17046646_reconstructed_balances_correct))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
