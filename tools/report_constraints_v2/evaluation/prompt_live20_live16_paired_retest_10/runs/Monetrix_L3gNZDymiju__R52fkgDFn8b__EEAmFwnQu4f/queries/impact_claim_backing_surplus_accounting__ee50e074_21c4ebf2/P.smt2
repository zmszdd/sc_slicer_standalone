; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce6f2b96c_accountant_is_configured () Bool)
(declare-fun ce6f2b96c_backing_surplus_accounting_monitoring_unavailable () Bool)
(declare-fun ce6f2b96c_blp_slot_registered_before_call () Bool)
(declare-fun ce6f2b96c_notify_vault_supply_called () Bool)
(declare-fun ce6f2b96c_slot_readable_and_active_verified () Bool)
(declare-fun ce6f2b96c_stale_slot_registered () Bool)
(assert
 (= ce6f2b96c_accountant_is_configured ce6f2b96c_accountant_is_configured))
(assert
 (= ce6f2b96c_backing_surplus_accounting_monitoring_unavailable ce6f2b96c_backing_surplus_accounting_monitoring_unavailable))
(assert
 (= ce6f2b96c_blp_slot_registered_before_call ce6f2b96c_blp_slot_registered_before_call))
(assert
 (= ce6f2b96c_notify_vault_supply_called ce6f2b96c_notify_vault_supply_called))
(assert
 (= ce6f2b96c_slot_readable_and_active_verified ce6f2b96c_slot_readable_and_active_verified))
(assert
 (= ce6f2b96c_stale_slot_registered ce6f2b96c_stale_slot_registered))
(define-fun report_preconditions () Bool (and ce6f2b96c_accountant_is_configured
     (not ce6f2b96c_blp_slot_registered_before_call)))
(define-fun report_safety () Bool (=> (and ce6f2b96c_accountant_is_configured
         ce6f2b96c_notify_vault_supply_called)
    ce6f2b96c_slot_readable_and_active_verified))
(define-fun report_effects () Bool (and ce6f2b96c_stale_slot_registered
     ce6f2b96c_backing_surplus_accounting_monitoring_unavailable
     ce6f2b96c_stale_slot_registered))
(assert report_preconditions)
(check-sat)
(get-model)
