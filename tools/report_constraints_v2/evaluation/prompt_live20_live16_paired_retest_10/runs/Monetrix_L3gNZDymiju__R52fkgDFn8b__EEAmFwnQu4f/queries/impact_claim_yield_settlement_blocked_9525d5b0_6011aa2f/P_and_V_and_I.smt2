; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c47cba869_accountant_is_configured () Bool)
(declare-fun c47cba869_blp_slot_registration_active () Bool)
(declare-fun c47cba869_hypercore_activation_asynchronous () Bool)
(declare-fun c47cba869_registration_promoted () Bool)
(declare-fun c47cba869_supplied_balance_read_successful () Bool)
(declare-fun c47cba869_yield_settlement_blocked () Bool)
(assert
 (= c47cba869_accountant_is_configured c47cba869_accountant_is_configured))
(assert
 (= c47cba869_blp_slot_registration_active c47cba869_blp_slot_registration_active))
(assert
 (= c47cba869_hypercore_activation_asynchronous c47cba869_hypercore_activation_asynchronous))
(assert
 (= c47cba869_registration_promoted c47cba869_registration_promoted))
(assert
 (= c47cba869_supplied_balance_read_successful c47cba869_supplied_balance_read_successful))
(assert
 (= c47cba869_yield_settlement_blocked c47cba869_yield_settlement_blocked))
(define-fun report_preconditions () Bool (and c47cba869_accountant_is_configured
     (not c47cba869_blp_slot_registration_active)))
(define-fun report_safety () Bool (=> (and c47cba869_hypercore_activation_asynchronous
         c47cba869_supplied_balance_read_successful)
    c47cba869_registration_promoted))
(define-fun report_effects () Bool c47cba869_yield_settlement_blocked)
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
(get-model)
