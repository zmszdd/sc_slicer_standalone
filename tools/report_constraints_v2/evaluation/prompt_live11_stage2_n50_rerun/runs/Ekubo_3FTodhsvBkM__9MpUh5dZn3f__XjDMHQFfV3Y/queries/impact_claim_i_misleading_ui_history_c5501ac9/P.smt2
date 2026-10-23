; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun cc200be5d_caller_is_not_holder () Bool)
(declare-fun cc200be5d_debited_holder_address () ReportAddress)
(declare-fun cc200be5d_event_from_address () ReportAddress)
(declare-fun cc200be5d_ui_history_misleading () Bool)
(assert
 (= cc200be5d_caller_is_not_holder cc200be5d_caller_is_not_holder))
(assert
 (= cc200be5d_debited_holder_address cc200be5d_debited_holder_address))
(assert
 (= cc200be5d_event_from_address cc200be5d_event_from_address))
(assert
 (= cc200be5d_ui_history_misleading cc200be5d_ui_history_misleading))
(define-fun report_preconditions () Bool cc200be5d_caller_is_not_holder)
(define-fun report_safety () Bool (=> cc200be5d_caller_is_not_holder
    (and (= cc200be5d_event_from_address cc200be5d_debited_holder_address)
         (not cc200be5d_ui_history_misleading))))
(define-fun report_effects () Bool (and cc200be5d_caller_is_not_holder
     (not (and (= cc200be5d_event_from_address cc200be5d_debited_holder_address)
               (not cc200be5d_ui_history_misleading)))))
(assert report_preconditions)
(check-sat)
(get-model)
