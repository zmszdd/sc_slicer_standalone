; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ceb6ead77_accountant_is_configured () Bool)
(declare-fun ceb6ead77_distributable_surplus_calculation_succeeds () Bool)
(declare-fun ceb6ead77_slot_active_registration_before_supply () Bool)
(declare-fun ceb6ead77_slot_readable_and_active_verified () Bool)
(declare-fun ceb6ead77_yield_settlement_blocked () Bool)
(assert
 (= ceb6ead77_accountant_is_configured ceb6ead77_accountant_is_configured))
(assert
 (= ceb6ead77_distributable_surplus_calculation_succeeds ceb6ead77_distributable_surplus_calculation_succeeds))
(assert
 (= ceb6ead77_slot_active_registration_before_supply ceb6ead77_slot_active_registration_before_supply))
(assert
 (= ceb6ead77_slot_readable_and_active_verified ceb6ead77_slot_readable_and_active_verified))
(assert
 (= ceb6ead77_yield_settlement_blocked ceb6ead77_yield_settlement_blocked))
(define-fun report_preconditions () Bool (and ceb6ead77_accountant_is_configured
     (not ceb6ead77_slot_active_registration_before_supply)))
(define-fun report_safety () Bool (=> ceb6ead77_slot_readable_and_active_verified
    ceb6ead77_distributable_surplus_calculation_succeeds))
(define-fun report_effects () Bool (and ceb6ead77_yield_settlement_blocked
     (not ceb6ead77_distributable_surplus_calculation_succeeds)))
