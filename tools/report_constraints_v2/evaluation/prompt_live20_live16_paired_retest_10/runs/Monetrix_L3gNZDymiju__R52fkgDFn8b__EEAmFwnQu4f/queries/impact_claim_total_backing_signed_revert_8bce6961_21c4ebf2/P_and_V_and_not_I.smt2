; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2e46b23a_accountant_configured () Bool)
(declare-fun c2e46b23a_later_strict_backing_reads_revert () Bool)
(declare-fun c2e46b23a_notify_vault_supply_called () Bool)
(declare-fun c2e46b23a_slot_active_registration_before () Bool)
(declare-fun c2e46b23a_slot_readable_and_active_verified () Bool)
(assert
 (= c2e46b23a_accountant_configured c2e46b23a_accountant_configured))
(assert
 (= c2e46b23a_later_strict_backing_reads_revert c2e46b23a_later_strict_backing_reads_revert))
(assert
 (= c2e46b23a_notify_vault_supply_called c2e46b23a_notify_vault_supply_called))
(assert
 (= c2e46b23a_slot_active_registration_before c2e46b23a_slot_active_registration_before))
(assert
 (= c2e46b23a_slot_readable_and_active_verified c2e46b23a_slot_readable_and_active_verified))
(define-fun report_preconditions () Bool (and c2e46b23a_accountant_configured
     (not c2e46b23a_slot_active_registration_before)))
(define-fun report_safety () Bool (=> (and c2e46b23a_notify_vault_supply_called
         c2e46b23a_slot_readable_and_active_verified)
    (not c2e46b23a_later_strict_backing_reads_revert)))
(define-fun report_effects () Bool (and c2e46b23a_later_strict_backing_reads_revert
     c2e46b23a_later_strict_backing_reads_revert))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
