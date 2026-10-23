; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3e52aa14_accountant_is_configured () Bool)
(declare-fun c3e52aa14_target_slot_activated_strict_read () Bool)
(declare-fun c3e52aa14_target_slot_active_registration_before () Bool)
(declare-fun c3e52aa14_target_slot_registered () Bool)
(assert
 (= c3e52aa14_accountant_is_configured c3e52aa14_accountant_is_configured))
(assert
 (= c3e52aa14_target_slot_activated_strict_read c3e52aa14_target_slot_activated_strict_read))
(assert
 (= c3e52aa14_target_slot_active_registration_before c3e52aa14_target_slot_active_registration_before))
(assert
 (= c3e52aa14_target_slot_registered c3e52aa14_target_slot_registered))
(define-fun report_preconditions () Bool (and c3e52aa14_accountant_is_configured
     (not c3e52aa14_target_slot_active_registration_before)))
(define-fun report_safety () Bool (=> c3e52aa14_target_slot_registered
    (=> c3e52aa14_target_slot_registered
        (= c3e52aa14_target_slot_activated_strict_read
           c3e52aa14_target_slot_registered))))
(define-fun report_effects () Bool (and c3e52aa14_target_slot_registered
     c3e52aa14_target_slot_registered
     (not (= c3e52aa14_target_slot_activated_strict_read
             c3e52aa14_target_slot_registered))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
