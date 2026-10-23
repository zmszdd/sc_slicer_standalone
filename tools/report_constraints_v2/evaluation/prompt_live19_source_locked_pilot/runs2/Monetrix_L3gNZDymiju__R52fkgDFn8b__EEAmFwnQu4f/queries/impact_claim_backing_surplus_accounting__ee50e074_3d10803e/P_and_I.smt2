; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c50e0a9e0_accountant_is_configured () Bool)
(declare-fun c50e0a9e0_notify_vault_supply_called () Bool)
(declare-fun c50e0a9e0_slot_active_registration_before () Bool)
(declare-fun c50e0a9e0_slot_readable_and_active_verified () Bool)
(declare-fun c50e0a9e0_stale_slot_registered () Bool)
(assert
 (= c50e0a9e0_accountant_is_configured c50e0a9e0_accountant_is_configured))
(assert
 (= c50e0a9e0_notify_vault_supply_called c50e0a9e0_notify_vault_supply_called))
(assert
 (= c50e0a9e0_slot_active_registration_before c50e0a9e0_slot_active_registration_before))
(assert
 (= c50e0a9e0_slot_readable_and_active_verified c50e0a9e0_slot_readable_and_active_verified))
(assert
 (= c50e0a9e0_stale_slot_registered c50e0a9e0_stale_slot_registered))
(define-fun report_preconditions () Bool (and c50e0a9e0_accountant_is_configured
     (not c50e0a9e0_slot_active_registration_before)))
(define-fun report_safety () Bool (=> c50e0a9e0_stale_slot_registered
    (=> (and c50e0a9e0_accountant_is_configured
             (not c50e0a9e0_slot_active_registration_before)
             c50e0a9e0_notify_vault_supply_called)
        c50e0a9e0_slot_readable_and_active_verified)))
(define-fun report_effects () Bool (and c50e0a9e0_stale_slot_registered
     c50e0a9e0_accountant_is_configured
     (not c50e0a9e0_slot_active_registration_before)
     c50e0a9e0_notify_vault_supply_called
     (not c50e0a9e0_slot_readable_and_active_verified)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
