; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c051d91a6_accountant_is_configured () Bool)
(declare-fun c051d91a6_accounting_settlement_reverts () Bool)
(declare-fun c051d91a6_active_registration_exists () Bool)
(declare-fun c051d91a6_supplied_slot_active () Bool)
(assert
 (= c051d91a6_accountant_is_configured c051d91a6_accountant_is_configured))
(assert
 (= c051d91a6_accounting_settlement_reverts c051d91a6_accounting_settlement_reverts))
(assert
 (= c051d91a6_active_registration_exists c051d91a6_active_registration_exists))
(assert
 (= c051d91a6_supplied_slot_active c051d91a6_supplied_slot_active))
(define-fun report_preconditions () Bool (and c051d91a6_accountant_is_configured
     (not c051d91a6_active_registration_exists)
     (not c051d91a6_supplied_slot_active)))
(define-fun report_safety () Bool (=> c051d91a6_accounting_settlement_reverts
    (=> (and c051d91a6_accountant_is_configured
             (not c051d91a6_active_registration_exists)
             (not c051d91a6_supplied_slot_active))
        (not c051d91a6_accounting_settlement_reverts))))
(define-fun report_effects () Bool (and c051d91a6_accounting_settlement_reverts
     c051d91a6_accountant_is_configured
     (not c051d91a6_active_registration_exists)
     (not c051d91a6_supplied_slot_active)
     (not (not c051d91a6_accounting_settlement_reverts))))
