; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cdcf3375a_accountant_is_configured () Bool)
(declare-fun cdcf3375a_active_registration_exists () Bool)
(declare-fun cdcf3375a_hypercore_slot_active_after_action () Bool)
(declare-fun cdcf3375a_registration_pending () Bool)
(declare-fun cdcf3375a_total_backing_signed_reverted () Bool)
(assert
 (= cdcf3375a_accountant_is_configured cdcf3375a_accountant_is_configured))
(assert
 (= cdcf3375a_active_registration_exists cdcf3375a_active_registration_exists))
(assert
 (= cdcf3375a_hypercore_slot_active_after_action cdcf3375a_hypercore_slot_active_after_action))
(assert
 (= cdcf3375a_registration_pending cdcf3375a_registration_pending))
(assert
 (= cdcf3375a_total_backing_signed_reverted cdcf3375a_total_backing_signed_reverted))
(define-fun report_preconditions () Bool (and cdcf3375a_accountant_is_configured
     (not cdcf3375a_active_registration_exists)
     (not cdcf3375a_hypercore_slot_active_after_action)))
(define-fun report_safety () Bool (=> cdcf3375a_total_backing_signed_reverted
    (=> (and cdcf3375a_accountant_is_configured
             (not cdcf3375a_active_registration_exists)
             (not cdcf3375a_hypercore_slot_active_after_action))
        (and cdcf3375a_registration_pending
             (not cdcf3375a_total_backing_signed_reverted)))))
(define-fun report_effects () Bool (and cdcf3375a_total_backing_signed_reverted
     cdcf3375a_accountant_is_configured
     (not cdcf3375a_active_registration_exists)
     (not cdcf3375a_hypercore_slot_active_after_action)
     (not (and cdcf3375a_registration_pending
               (not cdcf3375a_total_backing_signed_reverted)))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
