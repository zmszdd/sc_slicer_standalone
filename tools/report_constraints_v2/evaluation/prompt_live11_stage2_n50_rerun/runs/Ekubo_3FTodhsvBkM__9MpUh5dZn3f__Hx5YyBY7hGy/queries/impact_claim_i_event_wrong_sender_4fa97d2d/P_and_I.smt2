; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun ca7424e7d_event_from_address () ReportAddress)
(declare-fun ca7424e7d_from_holder_balance_debited () Bool)
(declare-fun ca7424e7d_from_parameter_address () ReportAddress)
(declare-fun ca7424e7d_transferfrom_invoked () Bool)
(assert
 (= ca7424e7d_event_from_address ca7424e7d_event_from_address))
(assert
 (= ca7424e7d_from_holder_balance_debited ca7424e7d_from_holder_balance_debited))
(assert
 (= ca7424e7d_from_parameter_address ca7424e7d_from_parameter_address))
(assert
 (= ca7424e7d_transferfrom_invoked ca7424e7d_transferfrom_invoked))
(define-fun report_preconditions () Bool (and ca7424e7d_transferfrom_invoked ca7424e7d_from_holder_balance_debited))
(define-fun report_safety () Bool (=> (and ca7424e7d_transferfrom_invoked ca7424e7d_from_holder_balance_debited)
    (= ca7424e7d_event_from_address ca7424e7d_from_parameter_address)))
(define-fun report_effects () Bool (and ca7424e7d_transferfrom_invoked
     ca7424e7d_from_holder_balance_debited
     (not (= ca7424e7d_event_from_address ca7424e7d_from_parameter_address))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
