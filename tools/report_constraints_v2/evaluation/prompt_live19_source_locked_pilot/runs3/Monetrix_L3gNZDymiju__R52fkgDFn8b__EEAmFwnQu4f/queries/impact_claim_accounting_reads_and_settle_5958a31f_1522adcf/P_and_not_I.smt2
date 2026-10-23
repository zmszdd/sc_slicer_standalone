; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c051d91a6_accountant_is_configured () Bool)
(declare-fun c051d91a6_accounting_reads_and_settlement_revert_occurred () Bool)
(declare-fun c051d91a6_notify_vault_supply_called () Bool)
(declare-fun c051d91a6_slot_active_registration_before_supply () Bool)
(declare-fun c051d91a6_slot_readable_and_active_verified () Bool)
(assert
 (= c051d91a6_accountant_is_configured c051d91a6_accountant_is_configured))
(assert
 (= c051d91a6_accounting_reads_and_settlement_revert_occurred c051d91a6_accounting_reads_and_settlement_revert_occurred))
(assert
 (= c051d91a6_notify_vault_supply_called c051d91a6_notify_vault_supply_called))
(assert
 (= c051d91a6_slot_active_registration_before_supply c051d91a6_slot_active_registration_before_supply))
(assert
 (= c051d91a6_slot_readable_and_active_verified c051d91a6_slot_readable_and_active_verified))
(define-fun report_preconditions () Bool (and c051d91a6_accountant_is_configured
     (not c051d91a6_slot_active_registration_before_supply)))
(define-fun report_safety () Bool (=> (and c051d91a6_notify_vault_supply_called
         c051d91a6_slot_readable_and_active_verified)
    (not c051d91a6_accounting_reads_and_settlement_revert_occurred)))
(define-fun report_effects () Bool (and c051d91a6_accounting_reads_and_settlement_revert_occurred
     c051d91a6_accounting_reads_and_settlement_revert_occurred))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
