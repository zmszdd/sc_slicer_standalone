; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ceb6ead77_accountant_is_configured () Bool)
(declare-fun ceb6ead77_active_registration_exists_before_supply () Bool)
(declare-fun ceb6ead77_distributable_surplus_calculation_succeeds () Bool)
(declare-fun ceb6ead77_hypercore_slot_active_after_action () Bool)
(declare-fun ceb6ead77_slot_verified_active_before_notify () Bool)
(declare-fun ceb6ead77_yield_settlement_blocked_observed () Bool)
(assert
 (= ceb6ead77_accountant_is_configured ceb6ead77_accountant_is_configured))
(assert
 (= ceb6ead77_active_registration_exists_before_supply ceb6ead77_active_registration_exists_before_supply))
(assert
 (= ceb6ead77_distributable_surplus_calculation_succeeds ceb6ead77_distributable_surplus_calculation_succeeds))
(assert
 (= ceb6ead77_hypercore_slot_active_after_action ceb6ead77_hypercore_slot_active_after_action))
(assert
 (= ceb6ead77_slot_verified_active_before_notify ceb6ead77_slot_verified_active_before_notify))
(assert
 (= ceb6ead77_yield_settlement_blocked_observed ceb6ead77_yield_settlement_blocked_observed))
(define-fun report_preconditions () Bool (and ceb6ead77_accountant_is_configured
     (not ceb6ead77_active_registration_exists_before_supply)
     (not ceb6ead77_hypercore_slot_active_after_action)))
(define-fun report_safety () Bool (=> ceb6ead77_yield_settlement_blocked_observed
    (=> ceb6ead77_slot_verified_active_before_notify
        ceb6ead77_distributable_surplus_calculation_succeeds)))
(define-fun report_effects () Bool (and ceb6ead77_yield_settlement_blocked_observed
     ceb6ead77_slot_verified_active_before_notify
     (not ceb6ead77_distributable_surplus_calculation_succeeds)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
