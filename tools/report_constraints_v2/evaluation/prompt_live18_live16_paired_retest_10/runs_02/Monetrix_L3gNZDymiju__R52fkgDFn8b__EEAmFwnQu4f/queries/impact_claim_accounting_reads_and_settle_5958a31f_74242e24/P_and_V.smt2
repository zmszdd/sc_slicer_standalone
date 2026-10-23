; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cecb89974_accountant_is_configured () Bool)
(declare-fun cecb89974_accountant_reads_and_settlement_revert () Bool)
(declare-fun cecb89974_hypercore_slot_active_after_action () Bool)
(declare-fun cecb89974_target_slot_registered_before () Bool)
(assert
 (= cecb89974_accountant_is_configured cecb89974_accountant_is_configured))
(assert
 (= cecb89974_accountant_reads_and_settlement_revert cecb89974_accountant_reads_and_settlement_revert))
(assert
 (= cecb89974_hypercore_slot_active_after_action cecb89974_hypercore_slot_active_after_action))
(assert
 (= cecb89974_target_slot_registered_before cecb89974_target_slot_registered_before))
(define-fun report_preconditions () Bool (and cecb89974_accountant_is_configured
     (not cecb89974_target_slot_registered_before)
     (not cecb89974_hypercore_slot_active_after_action)))
(define-fun report_safety () Bool (=> cecb89974_accountant_reads_and_settlement_revert
    (=> (and cecb89974_accountant_is_configured
             (not cecb89974_target_slot_registered_before)
             (not cecb89974_hypercore_slot_active_after_action))
        (not cecb89974_accountant_reads_and_settlement_revert))))
(define-fun report_effects () Bool (and cecb89974_accountant_reads_and_settlement_revert
     cecb89974_accountant_is_configured
     (not cecb89974_target_slot_registered_before)
     (not cecb89974_hypercore_slot_active_after_action)
     (not (not cecb89974_accountant_reads_and_settlement_revert))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
