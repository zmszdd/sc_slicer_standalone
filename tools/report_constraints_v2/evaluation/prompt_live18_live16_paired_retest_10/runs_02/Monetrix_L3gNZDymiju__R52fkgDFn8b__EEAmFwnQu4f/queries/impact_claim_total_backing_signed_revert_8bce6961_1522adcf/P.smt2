; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1b21f38a_accountant_is_configured () Bool)
(declare-fun c1b21f38a_active_registration_exists () Bool)
(declare-fun c1b21f38a_hypercore_slot_active_after_action () Bool)
(declare-fun c1b21f38a_notify_vault_supply_called () Bool)
(declare-fun c1b21f38a_total_backing_signed_reverts () Bool)
(assert
 (= c1b21f38a_accountant_is_configured c1b21f38a_accountant_is_configured))
(assert
 (= c1b21f38a_active_registration_exists c1b21f38a_active_registration_exists))
(assert
 (= c1b21f38a_hypercore_slot_active_after_action c1b21f38a_hypercore_slot_active_after_action))
(assert
 (= c1b21f38a_notify_vault_supply_called c1b21f38a_notify_vault_supply_called))
(assert
 (= c1b21f38a_total_backing_signed_reverts c1b21f38a_total_backing_signed_reverts))
(define-fun report_preconditions () Bool (and c1b21f38a_accountant_is_configured
     (not c1b21f38a_active_registration_exists)
     (not c1b21f38a_hypercore_slot_active_after_action)))
(define-fun report_safety () Bool (=> c1b21f38a_total_backing_signed_reverts
    (=> (and c1b21f38a_accountant_is_configured
             (not c1b21f38a_active_registration_exists)
             c1b21f38a_notify_vault_supply_called)
        (not c1b21f38a_total_backing_signed_reverts))))
(define-fun report_effects () Bool (and c1b21f38a_total_backing_signed_reverts
     c1b21f38a_accountant_is_configured
     (not c1b21f38a_active_registration_exists)
     c1b21f38a_notify_vault_supply_called
     (not (not c1b21f38a_total_backing_signed_reverts))))
(assert report_preconditions)
(check-sat)
(get-model)
