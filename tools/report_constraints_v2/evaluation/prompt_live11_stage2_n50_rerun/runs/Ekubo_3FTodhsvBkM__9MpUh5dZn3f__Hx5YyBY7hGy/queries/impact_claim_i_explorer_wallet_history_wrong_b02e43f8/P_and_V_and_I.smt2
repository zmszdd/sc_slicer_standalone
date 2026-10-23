; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun ccacb0278_actual_holder_address () ReportAddress)
(declare-fun ccacb0278_event_from_address () ReportAddress)
(declare-fun ccacb0278_explorer_history_correct () Bool)
(declare-fun ccacb0278_from_is_debited_holder () Bool)
(declare-fun ccacb0278_transferfrom_called () Bool)
(assert
 (= ccacb0278_actual_holder_address ccacb0278_actual_holder_address))
(assert
 (= ccacb0278_event_from_address ccacb0278_event_from_address))
(assert
 (= ccacb0278_explorer_history_correct ccacb0278_explorer_history_correct))
(assert
 (= ccacb0278_from_is_debited_holder ccacb0278_from_is_debited_holder))
(assert
 (= ccacb0278_transferfrom_called ccacb0278_transferfrom_called))
(define-fun report_preconditions () Bool (and ccacb0278_transferfrom_called ccacb0278_from_is_debited_holder))
(define-fun report_safety () Bool (=> (and ccacb0278_transferfrom_called ccacb0278_from_is_debited_holder)
    (and (= ccacb0278_event_from_address ccacb0278_actual_holder_address)
         ccacb0278_explorer_history_correct)))
(define-fun report_effects () Bool (and ccacb0278_transferfrom_called
     ccacb0278_from_is_debited_holder
     (not (and (= ccacb0278_event_from_address ccacb0278_actual_holder_address)
               ccacb0278_explorer_history_correct))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
