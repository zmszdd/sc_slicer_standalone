; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ced0b80ea_epoch_pending_withdrawals_locked () Bool)
(declare-fun ced0b80ea_user_has_pending_request_in_epoch_e () Bool)
(assert
 (= ced0b80ea_epoch_pending_withdrawals_locked ced0b80ea_epoch_pending_withdrawals_locked))
(assert
 (= ced0b80ea_user_has_pending_request_in_epoch_e ced0b80ea_user_has_pending_request_in_epoch_e))
(define-fun report_preconditions () Bool ced0b80ea_user_has_pending_request_in_epoch_e)
(define-fun report_safety () Bool (=> ced0b80ea_epoch_pending_withdrawals_locked
    (=> ced0b80ea_user_has_pending_request_in_epoch_e
        (not ced0b80ea_epoch_pending_withdrawals_locked))))
(define-fun report_effects () Bool (and ced0b80ea_epoch_pending_withdrawals_locked
     ced0b80ea_user_has_pending_request_in_epoch_e
     (not (not ced0b80ea_epoch_pending_withdrawals_locked))))
