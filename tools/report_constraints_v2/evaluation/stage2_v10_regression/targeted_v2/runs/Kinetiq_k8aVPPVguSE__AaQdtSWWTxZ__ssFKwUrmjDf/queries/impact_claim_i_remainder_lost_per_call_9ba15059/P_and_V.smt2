; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1ad8ee29_caller_has_manager_role () Bool)
(declare-fun c1ad8ee29_cancelled_withdrawal_amount () Int)
(declare-fun c1ad8ee29_remainder_retained () Bool)
(assert
 (= c1ad8ee29_caller_has_manager_role c1ad8ee29_caller_has_manager_role))
(assert
 (= c1ad8ee29_cancelled_withdrawal_amount c1ad8ee29_cancelled_withdrawal_amount))
(assert
 (= c1ad8ee29_remainder_retained c1ad8ee29_remainder_retained))
(define-fun report_preconditions () Bool (and (<= 0 c1ad8ee29_cancelled_withdrawal_amount)
     c1ad8ee29_caller_has_manager_role))
(define-fun report_safety () Bool (=> (and c1ad8ee29_caller_has_manager_role
         (<= 0 c1ad8ee29_cancelled_withdrawal_amount))
    c1ad8ee29_remainder_retained))
(define-fun report_effects () Bool (and c1ad8ee29_caller_has_manager_role
     (<= 0 c1ad8ee29_cancelled_withdrawal_amount)
     (not c1ad8ee29_remainder_retained)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
