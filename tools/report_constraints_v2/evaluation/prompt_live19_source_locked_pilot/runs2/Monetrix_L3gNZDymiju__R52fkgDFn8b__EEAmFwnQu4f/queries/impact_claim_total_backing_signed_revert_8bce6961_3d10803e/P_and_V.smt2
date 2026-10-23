; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c87ca029b_accountant_is_configured () Bool)
(declare-fun c87ca029b_notify_vault_supply_called () Bool)
(declare-fun c87ca029b_slot_readable_and_active_verified () Bool)
(declare-fun c87ca029b_slot_registration_active_before () Bool)
(declare-fun c87ca029b_total_backing_signed_reverts () Bool)
(assert
 (= c87ca029b_accountant_is_configured c87ca029b_accountant_is_configured))
(assert
 (= c87ca029b_notify_vault_supply_called c87ca029b_notify_vault_supply_called))
(assert
 (= c87ca029b_slot_readable_and_active_verified c87ca029b_slot_readable_and_active_verified))
(assert
 (= c87ca029b_slot_registration_active_before c87ca029b_slot_registration_active_before))
(assert
 (= c87ca029b_total_backing_signed_reverts c87ca029b_total_backing_signed_reverts))
(define-fun report_preconditions () Bool (and c87ca029b_accountant_is_configured
     (not c87ca029b_slot_registration_active_before)))
(define-fun report_safety () Bool (=> c87ca029b_total_backing_signed_reverts
    (=> c87ca029b_notify_vault_supply_called
        c87ca029b_slot_readable_and_active_verified)))
(define-fun report_effects () Bool (and c87ca029b_total_backing_signed_reverts
     c87ca029b_notify_vault_supply_called
     (not c87ca029b_slot_readable_and_active_verified)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
