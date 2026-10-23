; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8d499975_accountant_is_configured () Bool)
(declare-fun c8d499975_blp_slot_registration_active () Bool)
(declare-fun c8d499975_distributable_surplus_calculation_successful () Bool)
(declare-fun c8d499975_hypercore_activation_asynchronous () Bool)
(declare-fun c8d499975_registration_promoted () Bool)
(declare-fun c8d499975_supplied_balance_read_successful () Bool)
(assert
 (= c8d499975_accountant_is_configured c8d499975_accountant_is_configured))
(assert
 (= c8d499975_blp_slot_registration_active c8d499975_blp_slot_registration_active))
(assert
 (= c8d499975_distributable_surplus_calculation_successful c8d499975_distributable_surplus_calculation_successful))
(assert
 (= c8d499975_hypercore_activation_asynchronous c8d499975_hypercore_activation_asynchronous))
(assert
 (= c8d499975_registration_promoted c8d499975_registration_promoted))
(assert
 (= c8d499975_supplied_balance_read_successful c8d499975_supplied_balance_read_successful))
(define-fun report_preconditions () Bool (and c8d499975_accountant_is_configured
     (not c8d499975_blp_slot_registration_active)))
(define-fun report_safety () Bool (=> (not c8d499975_distributable_surplus_calculation_successful)
    (=> (and c8d499975_hypercore_activation_asynchronous
             c8d499975_supplied_balance_read_successful)
        c8d499975_registration_promoted)))
(define-fun report_effects () Bool (and (not c8d499975_distributable_surplus_calculation_successful)
     c8d499975_hypercore_activation_asynchronous
     c8d499975_supplied_balance_read_successful
     (not c8d499975_registration_promoted)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
