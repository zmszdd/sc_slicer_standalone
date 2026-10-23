; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0ae7887e_accountant_is_configured () Bool)
(declare-fun c0ae7887e_active_registration_exists_before () Bool)
(declare-fun c0ae7887e_backing_surplus_accounting_available () Bool)
(declare-fun c0ae7887e_hypercore_slot_active_after_action () Bool)
(declare-fun c0ae7887e_stale_slot_registered () Bool)
(assert
 (= c0ae7887e_accountant_is_configured c0ae7887e_accountant_is_configured))
(assert
 (= c0ae7887e_active_registration_exists_before c0ae7887e_active_registration_exists_before))
(assert
 (= c0ae7887e_backing_surplus_accounting_available c0ae7887e_backing_surplus_accounting_available))
(assert
 (= c0ae7887e_hypercore_slot_active_after_action c0ae7887e_hypercore_slot_active_after_action))
(assert
 (= c0ae7887e_stale_slot_registered c0ae7887e_stale_slot_registered))
(define-fun report_preconditions () Bool (and c0ae7887e_accountant_is_configured
     (not c0ae7887e_active_registration_exists_before)
     (not c0ae7887e_hypercore_slot_active_after_action)))
(define-fun report_safety () Bool (=> c0ae7887e_stale_slot_registered
    (=> (and c0ae7887e_accountant_is_configured
             (not c0ae7887e_active_registration_exists_before)
             (not c0ae7887e_hypercore_slot_active_after_action))
        c0ae7887e_backing_surplus_accounting_available)))
(define-fun report_effects () Bool (and c0ae7887e_stale_slot_registered
     c0ae7887e_accountant_is_configured
     (not c0ae7887e_active_registration_exists_before)
     (not c0ae7887e_hypercore_slot_active_after_action)
     (not c0ae7887e_backing_surplus_accounting_available)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
