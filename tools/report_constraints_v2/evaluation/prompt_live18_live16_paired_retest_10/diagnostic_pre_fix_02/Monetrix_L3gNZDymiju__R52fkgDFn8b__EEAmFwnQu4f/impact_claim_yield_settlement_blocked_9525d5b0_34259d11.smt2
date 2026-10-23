; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c422da9f9_accountant_is_configured () Bool)
(declare-fun c422da9f9_blp_slot_active_registration_before () Bool)
(declare-fun c422da9f9_distributable_surplus_succeeds () Bool)
(declare-fun c422da9f9_slot_readable_and_active_verified () Bool)
(declare-fun c422da9f9_yield_settlement_blocked_observed () Bool)
(assert
 (= c422da9f9_accountant_is_configured c422da9f9_accountant_is_configured))
(assert
 (= c422da9f9_blp_slot_active_registration_before c422da9f9_blp_slot_active_registration_before))
(assert
 (= c422da9f9_distributable_surplus_succeeds c422da9f9_distributable_surplus_succeeds))
(assert
 (= c422da9f9_slot_readable_and_active_verified c422da9f9_slot_readable_and_active_verified))
(assert
 (= c422da9f9_yield_settlement_blocked_observed c422da9f9_yield_settlement_blocked_observed))
(define-fun report_preconditions () Bool (and c422da9f9_accountant_is_configured
     (not c422da9f9_blp_slot_active_registration_before)))
(define-fun report_safety () Bool (=> c422da9f9_yield_settlement_blocked_observed
    (=> (and c422da9f9_accountant_is_configured
             c422da9f9_slot_readable_and_active_verified)
        c422da9f9_distributable_surplus_succeeds)))
(define-fun report_effects () Bool (and c422da9f9_yield_settlement_blocked_observed
     c422da9f9_accountant_is_configured
     c422da9f9_slot_readable_and_active_verified
     (not c422da9f9_distributable_surplus_succeeds)))
