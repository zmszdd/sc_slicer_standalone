; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd1d94a54_accountant_is_configured () Bool)
(declare-fun cd1d94a54_activation_asynchronous () Bool)
(declare-fun cd1d94a54_backing_surplus_accounting_available () Bool)
(declare-fun cd1d94a54_blp_slot_active_registration_before () Bool)
(declare-fun cd1d94a54_registration_pending_after_send () Bool)
(declare-fun cd1d94a54_registration_promoted () Bool)
(declare-fun cd1d94a54_stale_slot_registered () Bool)
(assert
 (= cd1d94a54_accountant_is_configured cd1d94a54_accountant_is_configured))
(assert
 (= cd1d94a54_activation_asynchronous cd1d94a54_activation_asynchronous))
(assert
 (= cd1d94a54_backing_surplus_accounting_available cd1d94a54_backing_surplus_accounting_available))
(assert
 (= cd1d94a54_blp_slot_active_registration_before cd1d94a54_blp_slot_active_registration_before))
(assert
 (= cd1d94a54_registration_pending_after_send cd1d94a54_registration_pending_after_send))
(assert
 (= cd1d94a54_registration_promoted cd1d94a54_registration_promoted))
(assert
 (= cd1d94a54_stale_slot_registered cd1d94a54_stale_slot_registered))
(define-fun report_preconditions () Bool (and cd1d94a54_accountant_is_configured
     (not cd1d94a54_blp_slot_active_registration_before)))
(define-fun report_safety () Bool (=> cd1d94a54_stale_slot_registered
    (=> (and cd1d94a54_accountant_is_configured
             (not cd1d94a54_blp_slot_active_registration_before)
             cd1d94a54_activation_asynchronous)
        (and cd1d94a54_registration_pending_after_send
             cd1d94a54_registration_promoted
             cd1d94a54_backing_surplus_accounting_available))))
(define-fun report_effects () Bool (and cd1d94a54_stale_slot_registered
     cd1d94a54_accountant_is_configured
     (not cd1d94a54_blp_slot_active_registration_before)
     cd1d94a54_activation_asynchronous
     (not (and cd1d94a54_registration_pending_after_send
               cd1d94a54_registration_promoted
               cd1d94a54_backing_surplus_accounting_available))))
