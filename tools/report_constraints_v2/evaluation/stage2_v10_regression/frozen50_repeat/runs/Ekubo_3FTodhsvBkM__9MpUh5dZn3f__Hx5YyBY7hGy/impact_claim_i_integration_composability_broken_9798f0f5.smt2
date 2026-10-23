; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3ff6ce5d_event_from_is_holder () Bool)
(declare-fun c3ff6ce5d_integration_credits_operator () Bool)
(declare-fun c3ff6ce5d_transferfrom_invoked () Bool)
(assert
 (= c3ff6ce5d_event_from_is_holder c3ff6ce5d_event_from_is_holder))
(assert
 (= c3ff6ce5d_integration_credits_operator c3ff6ce5d_integration_credits_operator))
(assert
 (= c3ff6ce5d_transferfrom_invoked c3ff6ce5d_transferfrom_invoked))
(define-fun report_preconditions () Bool (and c3ff6ce5d_transferfrom_invoked c3ff6ce5d_event_from_is_holder))
(define-fun report_safety () Bool (=> c3ff6ce5d_transferfrom_invoked
    (and c3ff6ce5d_event_from_is_holder
         (not c3ff6ce5d_integration_credits_operator))))
(define-fun report_effects () Bool (and c3ff6ce5d_transferfrom_invoked
     (not (and c3ff6ce5d_event_from_is_holder
               (not c3ff6ce5d_integration_credits_operator)))))
