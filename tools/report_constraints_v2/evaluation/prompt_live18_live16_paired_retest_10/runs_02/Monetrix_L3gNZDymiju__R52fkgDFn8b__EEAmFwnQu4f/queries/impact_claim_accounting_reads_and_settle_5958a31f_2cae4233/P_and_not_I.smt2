; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3b45308c_accountant_is_configured () Bool)
(declare-fun c3b45308c_accounting_reads_and_settlement_revert_occurs () Bool)
(declare-fun c3b45308c_active_registration_exists () Bool)
(declare-fun c3b45308c_hypercore_slot_inactive_after_action () Bool)
(assert
 (= c3b45308c_accountant_is_configured c3b45308c_accountant_is_configured))
(assert
 (= c3b45308c_accounting_reads_and_settlement_revert_occurs c3b45308c_accounting_reads_and_settlement_revert_occurs))
(assert
 (= c3b45308c_active_registration_exists c3b45308c_active_registration_exists))
(assert
 (= c3b45308c_hypercore_slot_inactive_after_action c3b45308c_hypercore_slot_inactive_after_action))
(define-fun report_preconditions () Bool (and c3b45308c_accountant_is_configured
     (not c3b45308c_active_registration_exists)
     c3b45308c_hypercore_slot_inactive_after_action))
(define-fun report_safety () Bool (=> c3b45308c_accounting_reads_and_settlement_revert_occurs
    (=> (and c3b45308c_accountant_is_configured
             (not c3b45308c_active_registration_exists)
             c3b45308c_hypercore_slot_inactive_after_action)
        (not c3b45308c_accounting_reads_and_settlement_revert_occurs))))
(define-fun report_effects () Bool (and c3b45308c_accounting_reads_and_settlement_revert_occurs
     c3b45308c_accountant_is_configured
     (not c3b45308c_active_registration_exists)
     c3b45308c_hypercore_slot_inactive_after_action
     (not (not c3b45308c_accounting_reads_and_settlement_revert_occurs))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
