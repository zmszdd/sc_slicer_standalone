; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0ae7887e_accountant_is_configured () Bool)
(declare-fun c0ae7887e_backing_surplus_accounting_monitoring_unavailable () Bool)
(declare-fun c0ae7887e_notify_vault_supply_called () Bool)
(declare-fun c0ae7887e_slot_active_registration_before_supply () Bool)
(declare-fun c0ae7887e_slot_readable_and_active_verified () Bool)
(declare-fun c0ae7887e_stale_slot_registered () Bool)
(assert
 (= c0ae7887e_accountant_is_configured c0ae7887e_accountant_is_configured))
(assert
 (= c0ae7887e_backing_surplus_accounting_monitoring_unavailable c0ae7887e_backing_surplus_accounting_monitoring_unavailable))
(assert
 (= c0ae7887e_notify_vault_supply_called c0ae7887e_notify_vault_supply_called))
(assert
 (= c0ae7887e_slot_active_registration_before_supply c0ae7887e_slot_active_registration_before_supply))
(assert
 (= c0ae7887e_slot_readable_and_active_verified c0ae7887e_slot_readable_and_active_verified))
(assert
 (= c0ae7887e_stale_slot_registered c0ae7887e_stale_slot_registered))
(define-fun report_preconditions () Bool (and c0ae7887e_accountant_is_configured
     (not c0ae7887e_slot_active_registration_before_supply)))
(define-fun report_safety () Bool (=> c0ae7887e_notify_vault_supply_called
    c0ae7887e_slot_readable_and_active_verified))
(define-fun report_effects () Bool (and c0ae7887e_backing_surplus_accounting_monitoring_unavailable
     c0ae7887e_stale_slot_registered))
(assert report_preconditions)
(check-sat)
(get-model)
