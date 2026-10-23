; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3e257254_accountant_is_configured () Bool)
(declare-fun c3e257254_backing_surplus_accounting_available () Bool)
(declare-fun c3e257254_hypercore_slot_active_after_action () Bool)
(declare-fun c3e257254_registration_promoted () Bool)
(declare-fun c3e257254_target_slot_registered_before () Bool)
(assert
 (= c3e257254_accountant_is_configured c3e257254_accountant_is_configured))
(assert
 (= c3e257254_backing_surplus_accounting_available c3e257254_backing_surplus_accounting_available))
(assert
 (= c3e257254_hypercore_slot_active_after_action c3e257254_hypercore_slot_active_after_action))
(assert
 (= c3e257254_registration_promoted c3e257254_registration_promoted))
(assert
 (= c3e257254_target_slot_registered_before c3e257254_target_slot_registered_before))
(define-fun report_preconditions () Bool (and c3e257254_accountant_is_configured
     (not c3e257254_target_slot_registered_before)
     (not c3e257254_hypercore_slot_active_after_action)))
(define-fun report_safety () Bool (=> (not c3e257254_backing_surplus_accounting_available)
    (=> (and c3e257254_accountant_is_configured
             (not c3e257254_target_slot_registered_before)
             (not c3e257254_hypercore_slot_active_after_action))
        (and (not c3e257254_registration_promoted)
             c3e257254_backing_surplus_accounting_available))))
(define-fun report_effects () Bool (and (not c3e257254_backing_surplus_accounting_available)
     c3e257254_accountant_is_configured
     (not c3e257254_target_slot_registered_before)
     (not c3e257254_hypercore_slot_active_after_action)
     (not (and (not c3e257254_registration_promoted)
               c3e257254_backing_surplus_accounting_available))))
