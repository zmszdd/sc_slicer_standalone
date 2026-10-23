; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc7c566fb_user_has_pending_request_in_epoch_e () Bool)
(declare-fun cc7c566fb_withdrawal_retrievable_via_standard_functions () Bool)
(declare-fun cc7c566fb_withdrawal_stuck () Bool)
(assert
 (= cc7c566fb_user_has_pending_request_in_epoch_e cc7c566fb_user_has_pending_request_in_epoch_e))
(assert
 (= cc7c566fb_withdrawal_retrievable_via_standard_functions cc7c566fb_withdrawal_retrievable_via_standard_functions))
(assert
 (= cc7c566fb_withdrawal_stuck cc7c566fb_withdrawal_stuck))
(define-fun report_preconditions () Bool cc7c566fb_user_has_pending_request_in_epoch_e)
(define-fun report_safety () Bool (=> cc7c566fb_withdrawal_stuck
    (=> cc7c566fb_user_has_pending_request_in_epoch_e
        cc7c566fb_withdrawal_retrievable_via_standard_functions)))
(define-fun report_effects () Bool (and cc7c566fb_withdrawal_stuck
     cc7c566fb_user_has_pending_request_in_epoch_e
     (not cc7c566fb_withdrawal_retrievable_via_standard_functions)))
