; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7f721bec_accountant_is_configured () Bool)
(declare-fun c7f721bec_active_registration_exists () Bool)
(declare-fun c7f721bec_distributable_surplus_calculation_succeeded () Bool)
(declare-fun c7f721bec_registration_pending () Bool)
(declare-fun c7f721bec_registration_promoted () Bool)
(declare-fun c7f721bec_supplied_balance_read_succeeded () Bool)
(assert
 (= c7f721bec_accountant_is_configured c7f721bec_accountant_is_configured))
(assert
 (= c7f721bec_active_registration_exists c7f721bec_active_registration_exists))
(assert
 (= c7f721bec_distributable_surplus_calculation_succeeded c7f721bec_distributable_surplus_calculation_succeeded))
(assert
 (= c7f721bec_registration_pending c7f721bec_registration_pending))
(assert
 (= c7f721bec_registration_promoted c7f721bec_registration_promoted))
(assert
 (= c7f721bec_supplied_balance_read_succeeded c7f721bec_supplied_balance_read_succeeded))
(define-fun report_preconditions () Bool (and c7f721bec_accountant_is_configured
     (not c7f721bec_active_registration_exists)))
(define-fun report_safety () Bool (=> (not c7f721bec_distributable_surplus_calculation_succeeded)
    (=> (and c7f721bec_accountant_is_configured
             (not c7f721bec_active_registration_exists)
             c7f721bec_registration_pending
             c7f721bec_supplied_balance_read_succeeded)
        c7f721bec_registration_promoted)))
(define-fun report_effects () Bool (and (not c7f721bec_distributable_surplus_calculation_succeeded)
     c7f721bec_accountant_is_configured
     (not c7f721bec_active_registration_exists)
     c7f721bec_registration_pending
     c7f721bec_supplied_balance_read_succeeded
     (not c7f721bec_registration_promoted)))
