; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3e2a2815_accountant_is_configured () Bool)
(declare-fun c3e2a2815_active_registration_exists_before () Bool)
(declare-fun c3e2a2815_backing_accounting_monitoring_unavailable () Bool)
(declare-fun c3e2a2815_hypercore_activation_asynchronous () Bool)
(declare-fun c3e2a2815_registration_promoted_after_successful_read () Bool)
(declare-fun c3e2a2815_stale_slot_registered () Bool)
(assert
 (= c3e2a2815_accountant_is_configured c3e2a2815_accountant_is_configured))
(assert
 (= c3e2a2815_active_registration_exists_before c3e2a2815_active_registration_exists_before))
(assert
 (= c3e2a2815_backing_accounting_monitoring_unavailable c3e2a2815_backing_accounting_monitoring_unavailable))
(assert
 (= c3e2a2815_hypercore_activation_asynchronous c3e2a2815_hypercore_activation_asynchronous))
(assert
 (= c3e2a2815_registration_promoted_after_successful_read c3e2a2815_registration_promoted_after_successful_read))
(assert
 (= c3e2a2815_stale_slot_registered c3e2a2815_stale_slot_registered))
(define-fun report_preconditions () Bool (and c3e2a2815_accountant_is_configured
     (not c3e2a2815_active_registration_exists_before)))
(define-fun report_safety () Bool (=> c3e2a2815_hypercore_activation_asynchronous
    (= c3e2a2815_registration_promoted_after_successful_read
       c3e2a2815_registration_promoted_after_successful_read)))
(define-fun report_effects () Bool (and c3e2a2815_stale_slot_registered
     c3e2a2815_backing_accounting_monitoring_unavailable
     c3e2a2815_stale_slot_registered))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
