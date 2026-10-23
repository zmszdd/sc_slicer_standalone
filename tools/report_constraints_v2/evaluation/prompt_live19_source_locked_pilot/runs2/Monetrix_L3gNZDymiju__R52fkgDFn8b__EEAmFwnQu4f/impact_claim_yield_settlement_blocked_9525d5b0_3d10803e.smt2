; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c48e1a162_accountant_is_configured () Bool)
(declare-fun c48e1a162_distributable_surplus_succeeds () Bool)
(declare-fun c48e1a162_notify_vault_supply_called () Bool)
(declare-fun c48e1a162_slot_active_registration_before () Bool)
(declare-fun c48e1a162_slot_readable_and_active_verified () Bool)
(declare-fun c48e1a162_yield_settlement_blocked () Bool)
(assert
 (= c48e1a162_accountant_is_configured c48e1a162_accountant_is_configured))
(assert
 (= c48e1a162_distributable_surplus_succeeds c48e1a162_distributable_surplus_succeeds))
(assert
 (= c48e1a162_notify_vault_supply_called c48e1a162_notify_vault_supply_called))
(assert
 (= c48e1a162_slot_active_registration_before c48e1a162_slot_active_registration_before))
(assert
 (= c48e1a162_slot_readable_and_active_verified c48e1a162_slot_readable_and_active_verified))
(assert
 (= c48e1a162_yield_settlement_blocked c48e1a162_yield_settlement_blocked))
(define-fun report_preconditions () Bool (and c48e1a162_accountant_is_configured
     (not c48e1a162_slot_active_registration_before)))
(define-fun report_safety () Bool (=> (and (not c48e1a162_distributable_surplus_succeeds)
         c48e1a162_yield_settlement_blocked)
    (=> (and c48e1a162_accountant_is_configured
             c48e1a162_notify_vault_supply_called)
        c48e1a162_slot_readable_and_active_verified)))
(define-fun report_effects () Bool (and (not c48e1a162_distributable_surplus_succeeds)
     c48e1a162_yield_settlement_blocked
     c48e1a162_accountant_is_configured
     c48e1a162_notify_vault_supply_called
     (not c48e1a162_slot_readable_and_active_verified)))
