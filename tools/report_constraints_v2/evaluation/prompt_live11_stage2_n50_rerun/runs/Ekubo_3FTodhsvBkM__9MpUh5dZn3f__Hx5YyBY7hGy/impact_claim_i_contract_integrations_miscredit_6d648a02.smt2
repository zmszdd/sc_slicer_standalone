; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-sort ReportAddress 0)
(declare-fun cc4a75711_debited_holder_address () ReportAddress)
(declare-fun cc4a75711_event_from_address () ReportAddress)
(declare-fun cc4a75711_from_is_debited_holder () Bool)
(declare-fun cc4a75711_integrations_miscredited () Bool)
(declare-fun cc4a75711_transferfrom_invoked () Bool)
(assert
 (= cc4a75711_debited_holder_address cc4a75711_debited_holder_address))
(assert
 (= cc4a75711_event_from_address cc4a75711_event_from_address))
(assert
 (= cc4a75711_from_is_debited_holder cc4a75711_from_is_debited_holder))
(assert
 (= cc4a75711_integrations_miscredited cc4a75711_integrations_miscredited))
(assert
 (= cc4a75711_transferfrom_invoked cc4a75711_transferfrom_invoked))
(define-fun report_preconditions () Bool (and cc4a75711_transferfrom_invoked cc4a75711_from_is_debited_holder))
(define-fun report_safety () Bool (=> (and cc4a75711_transferfrom_invoked cc4a75711_from_is_debited_holder)
    (and (= cc4a75711_event_from_address cc4a75711_debited_holder_address)
         (not cc4a75711_integrations_miscredited))))
(define-fun report_effects () Bool (and cc4a75711_transferfrom_invoked
     cc4a75711_from_is_debited_holder
     (not (and (= cc4a75711_event_from_address cc4a75711_debited_holder_address)
               (not cc4a75711_integrations_miscredited)))))
