; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca8afe1b4_accountant_is_configured () Bool)
(declare-fun ca8afe1b4_active_registration_exists_for_target_slot () Bool)
(declare-fun ca8afe1b4_target_slot_activated_strict_read () Bool)
(declare-fun ca8afe1b4_target_slot_registered () Bool)
(declare-fun ca8afe1b4_yield_settlement_blocked () Bool)
(assert
 (= ca8afe1b4_accountant_is_configured ca8afe1b4_accountant_is_configured))
(assert
 (= ca8afe1b4_active_registration_exists_for_target_slot ca8afe1b4_active_registration_exists_for_target_slot))
(assert
 (= ca8afe1b4_target_slot_activated_strict_read ca8afe1b4_target_slot_activated_strict_read))
(assert
 (= ca8afe1b4_target_slot_registered ca8afe1b4_target_slot_registered))
(assert
 (= ca8afe1b4_yield_settlement_blocked ca8afe1b4_yield_settlement_blocked))
(define-fun report_preconditions () Bool (and ca8afe1b4_accountant_is_configured
     (not ca8afe1b4_active_registration_exists_for_target_slot)))
(define-fun report_safety () Bool (=> ca8afe1b4_yield_settlement_blocked
    (=> (and ca8afe1b4_accountant_is_configured
             ca8afe1b4_target_slot_registered)
        ca8afe1b4_target_slot_activated_strict_read)))
(define-fun report_effects () Bool (and ca8afe1b4_yield_settlement_blocked
     ca8afe1b4_accountant_is_configured
     ca8afe1b4_target_slot_registered
     (not ca8afe1b4_target_slot_activated_strict_read)))
(assert report_preconditions)
(check-sat)
(get-model)
