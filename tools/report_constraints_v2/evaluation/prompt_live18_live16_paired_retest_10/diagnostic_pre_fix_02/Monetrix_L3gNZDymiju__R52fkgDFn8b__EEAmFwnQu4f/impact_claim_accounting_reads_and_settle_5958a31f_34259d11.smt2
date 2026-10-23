; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd19d752a_accountant_is_configured () Bool)
(declare-fun cd19d752a_accounting_reads_and_settlement_revert_occurred () Bool)
(declare-fun cd19d752a_blp_slot_registered_before_call () Bool)
(declare-fun cd19d752a_slot_readable_and_active_verified () Bool)
(assert
 (= cd19d752a_accountant_is_configured cd19d752a_accountant_is_configured))
(assert
 (= cd19d752a_accounting_reads_and_settlement_revert_occurred cd19d752a_accounting_reads_and_settlement_revert_occurred))
(assert
 (= cd19d752a_blp_slot_registered_before_call cd19d752a_blp_slot_registered_before_call))
(assert
 (= cd19d752a_slot_readable_and_active_verified cd19d752a_slot_readable_and_active_verified))
(define-fun report_preconditions () Bool (and cd19d752a_accountant_is_configured
     (not cd19d752a_blp_slot_registered_before_call)))
(define-fun report_safety () Bool (=> cd19d752a_accounting_reads_and_settlement_revert_occurred
    (=> cd19d752a_slot_readable_and_active_verified
        (not cd19d752a_accounting_reads_and_settlement_revert_occurred))))
(define-fun report_effects () Bool (and cd19d752a_accounting_reads_and_settlement_revert_occurred
     cd19d752a_slot_readable_and_active_verified
     (not (not cd19d752a_accounting_reads_and_settlement_revert_occurred))))
