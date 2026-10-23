; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cba192cd3_accountant_is_configured () Bool)
(declare-fun cba192cd3_active_registration_exists () Bool)
(declare-fun cba192cd3_distributable_surplus_calculated () Bool)
(declare-fun cba192cd3_hypercore_slot_active_after_action () Bool)
(declare-fun cba192cd3_registration_promoted () Bool)
(declare-fun cba192cd3_supplied_balance_read_succeeded () Bool)
(assert
 (= cba192cd3_accountant_is_configured cba192cd3_accountant_is_configured))
(assert
 (= cba192cd3_active_registration_exists cba192cd3_active_registration_exists))
(assert
 (= cba192cd3_distributable_surplus_calculated cba192cd3_distributable_surplus_calculated))
(assert
 (= cba192cd3_hypercore_slot_active_after_action cba192cd3_hypercore_slot_active_after_action))
(assert
 (= cba192cd3_registration_promoted cba192cd3_registration_promoted))
(assert
 (= cba192cd3_supplied_balance_read_succeeded cba192cd3_supplied_balance_read_succeeded))
(define-fun report_preconditions () Bool (and cba192cd3_accountant_is_configured
     (not cba192cd3_active_registration_exists)
     (not cba192cd3_hypercore_slot_active_after_action)))
(define-fun report_safety () Bool (=> (not cba192cd3_distributable_surplus_calculated)
    (=> (and cba192cd3_accountant_is_configured
             (not cba192cd3_active_registration_exists)
             (not cba192cd3_hypercore_slot_active_after_action))
        (and (not cba192cd3_registration_promoted)
             (not cba192cd3_supplied_balance_read_succeeded)))))
(define-fun report_effects () Bool (and (not cba192cd3_distributable_surplus_calculated)
     cba192cd3_accountant_is_configured
     (not cba192cd3_active_registration_exists)
     (not cba192cd3_hypercore_slot_active_after_action)
     (not (and (not cba192cd3_registration_promoted)
               (not cba192cd3_supplied_balance_read_succeeded)))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
