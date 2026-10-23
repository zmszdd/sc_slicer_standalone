; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0b5253dd_accountant_is_configured () Bool)
(declare-fun c0b5253dd_notify_vault_supply_called () Bool)
(declare-fun c0b5253dd_slot_readable_and_active_verified () Bool)
(declare-fun c0b5253dd_slot_registration_active_before_call () Bool)
(declare-fun c0b5253dd_yield_settlement_blocked_occurred () Bool)
(assert
 (= c0b5253dd_accountant_is_configured c0b5253dd_accountant_is_configured))
(assert
 (= c0b5253dd_notify_vault_supply_called c0b5253dd_notify_vault_supply_called))
(assert
 (= c0b5253dd_slot_readable_and_active_verified c0b5253dd_slot_readable_and_active_verified))
(assert
 (= c0b5253dd_slot_registration_active_before_call c0b5253dd_slot_registration_active_before_call))
(assert
 (= c0b5253dd_yield_settlement_blocked_occurred c0b5253dd_yield_settlement_blocked_occurred))
(define-fun report_preconditions () Bool (and c0b5253dd_accountant_is_configured
     (not c0b5253dd_slot_registration_active_before_call)))
(define-fun report_safety () Bool (=> (and c0b5253dd_notify_vault_supply_called
         c0b5253dd_slot_readable_and_active_verified)
    c0b5253dd_slot_readable_and_active_verified))
(define-fun report_effects () Bool c0b5253dd_yield_settlement_blocked_occurred)
