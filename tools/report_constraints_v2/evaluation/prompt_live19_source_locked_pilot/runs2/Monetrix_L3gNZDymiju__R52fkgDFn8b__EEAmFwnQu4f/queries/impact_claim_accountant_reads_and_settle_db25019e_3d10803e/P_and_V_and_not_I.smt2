; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c09c4da03_accountant_is_configured () Bool)
(declare-fun c09c4da03_accountant_reads_and_settlement_revert_occurred () Bool)
(declare-fun c09c4da03_slot_active_registration_before () Bool)
(declare-fun c09c4da03_slot_readable_and_active_verified () Bool)
(assert
 (= c09c4da03_accountant_is_configured c09c4da03_accountant_is_configured))
(assert
 (= c09c4da03_accountant_reads_and_settlement_revert_occurred c09c4da03_accountant_reads_and_settlement_revert_occurred))
(assert
 (= c09c4da03_slot_active_registration_before c09c4da03_slot_active_registration_before))
(assert
 (= c09c4da03_slot_readable_and_active_verified c09c4da03_slot_readable_and_active_verified))
(define-fun report_preconditions () Bool (and c09c4da03_accountant_is_configured
     (not c09c4da03_slot_active_registration_before)))
(define-fun report_safety () Bool (=> c09c4da03_accountant_reads_and_settlement_revert_occurred
    (=> c09c4da03_slot_readable_and_active_verified
        (not c09c4da03_accountant_reads_and_settlement_revert_occurred))))
(define-fun report_effects () Bool (and c09c4da03_accountant_reads_and_settlement_revert_occurred
     c09c4da03_slot_readable_and_active_verified
     (not (not c09c4da03_accountant_reads_and_settlement_revert_occurred))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
