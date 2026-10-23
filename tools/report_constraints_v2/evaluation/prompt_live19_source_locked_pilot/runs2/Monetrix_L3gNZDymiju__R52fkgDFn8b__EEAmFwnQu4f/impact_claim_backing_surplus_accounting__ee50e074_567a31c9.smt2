; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c160198c6_accountant_is_configured () Bool)
(declare-fun c160198c6_blp_slot_active_registration_before () Bool)
(declare-fun c160198c6_hypercore_activation_asynchronous () Bool)
(declare-fun c160198c6_registration_pending () Bool)
(declare-fun c160198c6_registration_promoted () Bool)
(declare-fun c160198c6_stale_slot_registered () Bool)
(declare-fun c160198c6_supplied_balance_read_successful () Bool)
(assert
 (= c160198c6_accountant_is_configured c160198c6_accountant_is_configured))
(assert
 (= c160198c6_blp_slot_active_registration_before c160198c6_blp_slot_active_registration_before))
(assert
 (= c160198c6_hypercore_activation_asynchronous c160198c6_hypercore_activation_asynchronous))
(assert
 (= c160198c6_registration_pending c160198c6_registration_pending))
(assert
 (= c160198c6_registration_promoted c160198c6_registration_promoted))
(assert
 (= c160198c6_stale_slot_registered c160198c6_stale_slot_registered))
(assert
 (= c160198c6_supplied_balance_read_successful c160198c6_supplied_balance_read_successful))
(define-fun report_preconditions () Bool (and c160198c6_accountant_is_configured
     (not c160198c6_blp_slot_active_registration_before)))
(define-fun report_safety () Bool (=> c160198c6_stale_slot_registered
    (=> (and c160198c6_hypercore_activation_asynchronous
             c160198c6_registration_pending)
        (= c160198c6_registration_promoted
           c160198c6_supplied_balance_read_successful))))
(define-fun report_effects () Bool (and c160198c6_stale_slot_registered
     c160198c6_hypercore_activation_asynchronous
     c160198c6_registration_pending
     (not (= c160198c6_registration_promoted
             c160198c6_supplied_balance_read_successful))))
