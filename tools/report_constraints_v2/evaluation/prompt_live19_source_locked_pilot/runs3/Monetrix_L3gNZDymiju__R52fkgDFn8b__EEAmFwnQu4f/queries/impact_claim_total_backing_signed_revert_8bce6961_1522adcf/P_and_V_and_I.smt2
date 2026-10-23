; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1b21f38a_accountant_is_configured () Bool)
(declare-fun c1b21f38a_slot_active_registration_before_supply () Bool)
(declare-fun c1b21f38a_slot_readable_and_active_verified () Bool)
(declare-fun c1b21f38a_total_backing_signed_reverts () Bool)
(assert
 (= c1b21f38a_accountant_is_configured c1b21f38a_accountant_is_configured))
(assert
 (= c1b21f38a_slot_active_registration_before_supply c1b21f38a_slot_active_registration_before_supply))
(assert
 (= c1b21f38a_slot_readable_and_active_verified c1b21f38a_slot_readable_and_active_verified))
(assert
 (= c1b21f38a_total_backing_signed_reverts c1b21f38a_total_backing_signed_reverts))
(define-fun report_preconditions () Bool (and c1b21f38a_accountant_is_configured
     (not c1b21f38a_slot_active_registration_before_supply)))
(define-fun report_safety () Bool (=> c1b21f38a_slot_readable_and_active_verified
    c1b21f38a_slot_readable_and_active_verified))
(define-fun report_effects () Bool (and c1b21f38a_total_backing_signed_reverts
     c1b21f38a_total_backing_signed_reverts))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
(get-model)
