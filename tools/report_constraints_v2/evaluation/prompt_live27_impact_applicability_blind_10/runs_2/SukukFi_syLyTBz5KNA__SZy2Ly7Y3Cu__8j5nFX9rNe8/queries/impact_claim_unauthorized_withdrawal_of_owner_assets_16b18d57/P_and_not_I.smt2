; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c01ad2a76_caller_has_allowance () Bool)
(declare-fun c01ad2a76_caller_is_owner () Bool)
(declare-fun c01ad2a76_withdrawal_completed () Bool)
(assert
 (= c01ad2a76_caller_has_allowance c01ad2a76_caller_has_allowance))
(assert
 (= c01ad2a76_caller_is_owner c01ad2a76_caller_is_owner))
(assert
 (= c01ad2a76_withdrawal_completed c01ad2a76_withdrawal_completed))
(define-fun report_preconditions () Bool (and (not c01ad2a76_caller_is_owner) (not c01ad2a76_caller_has_allowance)))
(define-fun report_safety () Bool (=> c01ad2a76_withdrawal_completed
    (=> c01ad2a76_withdrawal_completed
        (or c01ad2a76_caller_is_owner c01ad2a76_caller_has_allowance))))
(define-fun report_effects () Bool (and c01ad2a76_withdrawal_completed
     c01ad2a76_withdrawal_completed
     (not (or c01ad2a76_caller_is_owner c01ad2a76_caller_has_allowance))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
