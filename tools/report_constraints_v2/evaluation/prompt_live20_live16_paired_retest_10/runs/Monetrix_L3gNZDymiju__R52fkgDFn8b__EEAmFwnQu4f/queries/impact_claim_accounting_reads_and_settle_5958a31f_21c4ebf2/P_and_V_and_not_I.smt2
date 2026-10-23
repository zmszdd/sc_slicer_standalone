; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c441be20a_accountant_is_configured () Bool)
(declare-fun c441be20a_accounting_reads_and_settlement_revert_occurred () Bool)
(declare-fun c441be20a_blp_slot_active_registration_before () Bool)
(declare-fun c441be20a_notify_vault_supply_called () Bool)
(declare-fun c441be20a_supplied_slot_readable_and_active_verified () Bool)
(assert
 (= c441be20a_accountant_is_configured c441be20a_accountant_is_configured))
(assert
 (= c441be20a_accounting_reads_and_settlement_revert_occurred c441be20a_accounting_reads_and_settlement_revert_occurred))
(assert
 (= c441be20a_blp_slot_active_registration_before c441be20a_blp_slot_active_registration_before))
(assert
 (= c441be20a_notify_vault_supply_called c441be20a_notify_vault_supply_called))
(assert
 (= c441be20a_supplied_slot_readable_and_active_verified c441be20a_supplied_slot_readable_and_active_verified))
(define-fun report_preconditions () Bool (and c441be20a_accountant_is_configured
     (not c441be20a_blp_slot_active_registration_before)))
(define-fun report_safety () Bool (=> (and c441be20a_notify_vault_supply_called
         c441be20a_supplied_slot_readable_and_active_verified)
    (not c441be20a_accounting_reads_and_settlement_revert_occurred)))
(define-fun report_effects () Bool (and c441be20a_accounting_reads_and_settlement_revert_occurred
     c441be20a_accounting_reads_and_settlement_revert_occurred))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
