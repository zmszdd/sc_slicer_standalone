; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2f01d028_accountant_is_configured () Bool)
(declare-fun c2f01d028_active_registration_exists_for_target_slot () Bool)
(declare-fun c2f01d028_slot_is_activated_strict_read () Bool)
(declare-fun c2f01d028_total_backing_signed_reverts_occurred () Bool)
(assert
 (= c2f01d028_accountant_is_configured c2f01d028_accountant_is_configured))
(assert
 (= c2f01d028_active_registration_exists_for_target_slot c2f01d028_active_registration_exists_for_target_slot))
(assert
 (= c2f01d028_slot_is_activated_strict_read c2f01d028_slot_is_activated_strict_read))
(assert
 (= c2f01d028_total_backing_signed_reverts_occurred c2f01d028_total_backing_signed_reverts_occurred))
(define-fun report_preconditions () Bool (and c2f01d028_accountant_is_configured
     (not c2f01d028_active_registration_exists_for_target_slot)))
(define-fun report_safety () Bool (=> c2f01d028_total_backing_signed_reverts_occurred
    (=> (and c2f01d028_accountant_is_configured
             (not c2f01d028_active_registration_exists_for_target_slot))
        c2f01d028_slot_is_activated_strict_read)))
(define-fun report_effects () Bool (and c2f01d028_total_backing_signed_reverts_occurred
     c2f01d028_accountant_is_configured
     (not c2f01d028_active_registration_exists_for_target_slot)
     (not c2f01d028_slot_is_activated_strict_read)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
