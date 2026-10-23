; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3ec1974f_accountant_is_configured () Bool)
(declare-fun c3ec1974f_active_registration_exists () Bool)
(declare-fun c3ec1974f_hypercore_slot_active () Bool)
(declare-fun c3ec1974f_registered_slot_readable () Bool)
(declare-fun c3ec1974f_total_backing_signed_reverts () Bool)
(assert
 (= c3ec1974f_accountant_is_configured c3ec1974f_accountant_is_configured))
(assert
 (= c3ec1974f_active_registration_exists c3ec1974f_active_registration_exists))
(assert
 (= c3ec1974f_hypercore_slot_active c3ec1974f_hypercore_slot_active))
(assert
 (= c3ec1974f_registered_slot_readable c3ec1974f_registered_slot_readable))
(assert
 (= c3ec1974f_total_backing_signed_reverts c3ec1974f_total_backing_signed_reverts))
(define-fun report_preconditions () Bool (and c3ec1974f_accountant_is_configured
     (not c3ec1974f_active_registration_exists)
     (not c3ec1974f_hypercore_slot_active)))
(define-fun report_safety () Bool (=> c3ec1974f_total_backing_signed_reverts
    (=> (and c3ec1974f_accountant_is_configured
             c3ec1974f_registered_slot_readable)
        (not c3ec1974f_total_backing_signed_reverts))))
(define-fun report_effects () Bool (and c3ec1974f_total_backing_signed_reverts
     c3ec1974f_accountant_is_configured
     c3ec1974f_registered_slot_readable
     (not (not c3ec1974f_total_backing_signed_reverts))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
