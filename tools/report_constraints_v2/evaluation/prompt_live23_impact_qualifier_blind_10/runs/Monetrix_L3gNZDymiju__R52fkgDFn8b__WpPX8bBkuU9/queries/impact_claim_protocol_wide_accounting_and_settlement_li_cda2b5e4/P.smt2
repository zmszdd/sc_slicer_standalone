; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6e70e940_accounting_reads_revert_after_unwind () Bool)
(declare-fun c6e70e940_blp_lifecycle_supply_then_full_unwind () Bool)
(declare-fun c6e70e940_vault_supplied_slot_registered () Bool)
(assert
 (= c6e70e940_accounting_reads_revert_after_unwind c6e70e940_accounting_reads_revert_after_unwind))
(assert
 (= c6e70e940_blp_lifecycle_supply_then_full_unwind c6e70e940_blp_lifecycle_supply_then_full_unwind))
(assert
 (= c6e70e940_vault_supplied_slot_registered c6e70e940_vault_supplied_slot_registered))
(define-fun report_preconditions () Bool (and c6e70e940_vault_supplied_slot_registered
     c6e70e940_blp_lifecycle_supply_then_full_unwind))
(define-fun report_safety () Bool (=> c6e70e940_accounting_reads_revert_after_unwind
    (=> (and c6e70e940_vault_supplied_slot_registered
             c6e70e940_blp_lifecycle_supply_then_full_unwind)
        (not c6e70e940_accounting_reads_revert_after_unwind))))
(define-fun report_effects () Bool (and c6e70e940_accounting_reads_revert_after_unwind
     c6e70e940_vault_supplied_slot_registered
     c6e70e940_blp_lifecycle_supply_then_full_unwind
     (not (not c6e70e940_accounting_reads_revert_after_unwind))))
(assert report_preconditions)
(check-sat)
(get-model)
