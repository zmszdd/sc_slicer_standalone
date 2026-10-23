; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce3d2a949_accountant_is_configured () Bool)
(declare-fun ce3d2a949_blp_slot_active_registration_before () Bool)
(declare-fun ce3d2a949_blp_slot_readable_and_active_verified () Bool)
(declare-fun ce3d2a949_total_backing_signed_reverts_after () Bool)
(assert
 (= ce3d2a949_accountant_is_configured ce3d2a949_accountant_is_configured))
(assert
 (= ce3d2a949_blp_slot_active_registration_before ce3d2a949_blp_slot_active_registration_before))
(assert
 (= ce3d2a949_blp_slot_readable_and_active_verified ce3d2a949_blp_slot_readable_and_active_verified))
(assert
 (= ce3d2a949_total_backing_signed_reverts_after ce3d2a949_total_backing_signed_reverts_after))
(define-fun report_preconditions () Bool (and ce3d2a949_accountant_is_configured
     (not ce3d2a949_blp_slot_active_registration_before)))
(define-fun report_safety () Bool (=> ce3d2a949_total_backing_signed_reverts_after
    (=> (and ce3d2a949_accountant_is_configured
             (not ce3d2a949_blp_slot_active_registration_before))
        ce3d2a949_blp_slot_readable_and_active_verified)))
(define-fun report_effects () Bool (and ce3d2a949_total_backing_signed_reverts_after
     ce3d2a949_accountant_is_configured
     (not ce3d2a949_blp_slot_active_registration_before)
     (not ce3d2a949_blp_slot_readable_and_active_verified)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
