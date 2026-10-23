; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cba192cd3_accountant_is_configured () Bool)
(declare-fun cba192cd3_blp_slot_registration_active () Bool)
(declare-fun cba192cd3_distributable_surplus_calculation_successful () Bool)
(declare-fun cba192cd3_hypercore_activation_asynchronous () Bool)
(declare-fun cba192cd3_registration_promoted () Bool)
(declare-fun cba192cd3_supplied_balance_read_successful () Bool)
(declare-fun cba192cd3_yield_settlement_blocked () Bool)
(assert
 (= cba192cd3_accountant_is_configured cba192cd3_accountant_is_configured))
(assert
 (= cba192cd3_blp_slot_registration_active cba192cd3_blp_slot_registration_active))
(assert
 (= cba192cd3_distributable_surplus_calculation_successful cba192cd3_distributable_surplus_calculation_successful))
(assert
 (= cba192cd3_hypercore_activation_asynchronous cba192cd3_hypercore_activation_asynchronous))
(assert
 (= cba192cd3_registration_promoted cba192cd3_registration_promoted))
(assert
 (= cba192cd3_supplied_balance_read_successful cba192cd3_supplied_balance_read_successful))
(assert
 (= cba192cd3_yield_settlement_blocked cba192cd3_yield_settlement_blocked))
(define-fun report_preconditions () Bool (and cba192cd3_accountant_is_configured
     (not cba192cd3_blp_slot_registration_active)))
(define-fun report_safety () Bool (=> (and cba192cd3_hypercore_activation_asynchronous
         (not cba192cd3_blp_slot_registration_active))
    (and (not cba192cd3_registration_promoted)
         cba192cd3_supplied_balance_read_successful)))
(define-fun report_effects () Bool (and cba192cd3_yield_settlement_blocked
     (not cba192cd3_distributable_surplus_calculation_successful)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
(get-model)
