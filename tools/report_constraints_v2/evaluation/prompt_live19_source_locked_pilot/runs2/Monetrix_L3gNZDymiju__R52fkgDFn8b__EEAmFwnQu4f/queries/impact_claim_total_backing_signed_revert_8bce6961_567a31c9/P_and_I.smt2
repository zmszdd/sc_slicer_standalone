; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c289fd6a3_accountant_is_configured () Bool)
(declare-fun c289fd6a3_active_registration_exists () Bool)
(declare-fun c289fd6a3_hypercore_activation_asynchronous () Bool)
(declare-fun c289fd6a3_registration_promoted () Bool)
(declare-fun c289fd6a3_supplied_balance_read_succeeded () Bool)
(declare-fun c289fd6a3_total_backing_signed_reverts () Bool)
(assert
 (= c289fd6a3_accountant_is_configured c289fd6a3_accountant_is_configured))
(assert
 (= c289fd6a3_active_registration_exists c289fd6a3_active_registration_exists))
(assert
 (= c289fd6a3_hypercore_activation_asynchronous c289fd6a3_hypercore_activation_asynchronous))
(assert
 (= c289fd6a3_registration_promoted c289fd6a3_registration_promoted))
(assert
 (= c289fd6a3_supplied_balance_read_succeeded c289fd6a3_supplied_balance_read_succeeded))
(assert
 (= c289fd6a3_total_backing_signed_reverts c289fd6a3_total_backing_signed_reverts))
(define-fun report_preconditions () Bool (and c289fd6a3_accountant_is_configured
     (not c289fd6a3_active_registration_exists)))
(define-fun report_safety () Bool (=> c289fd6a3_total_backing_signed_reverts
    (=> (and c289fd6a3_hypercore_activation_asynchronous
             c289fd6a3_supplied_balance_read_succeeded)
        c289fd6a3_registration_promoted)))
(define-fun report_effects () Bool (and c289fd6a3_total_backing_signed_reverts
     c289fd6a3_hypercore_activation_asynchronous
     c289fd6a3_supplied_balance_read_succeeded
     (not c289fd6a3_registration_promoted)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
