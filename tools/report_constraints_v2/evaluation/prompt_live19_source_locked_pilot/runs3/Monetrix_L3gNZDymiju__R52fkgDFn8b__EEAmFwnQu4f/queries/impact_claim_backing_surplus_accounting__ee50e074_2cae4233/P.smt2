; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3e257254_accountant_is_configured () Bool)
(declare-fun c3e257254_active_registration_exists () Bool)
(declare-fun c3e257254_backing_surplus_accounting_monitoring_unavailable () Bool)
(declare-fun c3e257254_hypercore_activation_asynchronous () Bool)
(declare-fun c3e257254_registration_pending () Bool)
(declare-fun c3e257254_stale_slot_registered () Bool)
(declare-fun c3e257254_supplied_balance_read_successful () Bool)
(assert
 (= c3e257254_accountant_is_configured c3e257254_accountant_is_configured))
(assert
 (= c3e257254_active_registration_exists c3e257254_active_registration_exists))
(assert
 (= c3e257254_backing_surplus_accounting_monitoring_unavailable c3e257254_backing_surplus_accounting_monitoring_unavailable))
(assert
 (= c3e257254_hypercore_activation_asynchronous c3e257254_hypercore_activation_asynchronous))
(assert
 (= c3e257254_registration_pending c3e257254_registration_pending))
(assert
 (= c3e257254_stale_slot_registered c3e257254_stale_slot_registered))
(assert
 (= c3e257254_supplied_balance_read_successful c3e257254_supplied_balance_read_successful))
(define-fun report_preconditions () Bool (and c3e257254_accountant_is_configured
     (not c3e257254_active_registration_exists)))
(define-fun report_safety () Bool (=> (and c3e257254_hypercore_activation_asynchronous
         (not c3e257254_supplied_balance_read_successful))
    (= c3e257254_registration_pending c3e257254_registration_pending)))
(define-fun report_effects () Bool (and c3e257254_backing_surplus_accounting_monitoring_unavailable
     c3e257254_stale_slot_registered))
(assert report_preconditions)
(check-sat)
(get-model)
