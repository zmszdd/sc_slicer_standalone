; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7e443c13_accountant_configured () Bool)
(declare-fun c7e443c13_backing_surplus_accounting_monitoring_available () Bool)
(declare-fun c7e443c13_slot_active_registration_before () Bool)
(declare-fun c7e443c13_slot_readable_and_active_verified () Bool)
(assert
 (= c7e443c13_accountant_configured c7e443c13_accountant_configured))
(assert
 (= c7e443c13_backing_surplus_accounting_monitoring_available c7e443c13_backing_surplus_accounting_monitoring_available))
(assert
 (= c7e443c13_slot_active_registration_before c7e443c13_slot_active_registration_before))
(assert
 (= c7e443c13_slot_readable_and_active_verified c7e443c13_slot_readable_and_active_verified))
(define-fun report_preconditions () Bool (and c7e443c13_accountant_configured
     (not c7e443c13_slot_active_registration_before)))
(define-fun report_safety () Bool (=> (not c7e443c13_backing_surplus_accounting_monitoring_available)
    (=> c7e443c13_slot_readable_and_active_verified
        c7e443c13_backing_surplus_accounting_monitoring_available)))
(define-fun report_effects () Bool (and (not c7e443c13_backing_surplus_accounting_monitoring_available)
     c7e443c13_slot_readable_and_active_verified
     (not c7e443c13_backing_surplus_accounting_monitoring_available)))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
