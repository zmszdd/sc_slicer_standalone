; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cacba81ed_caller_has_manager_role () Bool)
(declare-fun cacba81ed_cancelled_withdrawal_amount () Int)
(declare-fun cacba81ed_remainder_outside_accounting () Bool)
(assert
 (= cacba81ed_caller_has_manager_role cacba81ed_caller_has_manager_role))
(assert
 (= cacba81ed_cancelled_withdrawal_amount cacba81ed_cancelled_withdrawal_amount))
(assert
 (= cacba81ed_remainder_outside_accounting cacba81ed_remainder_outside_accounting))
(define-fun report_preconditions () Bool (and (<= 0 cacba81ed_cancelled_withdrawal_amount)
     cacba81ed_caller_has_manager_role))
(define-fun report_safety () Bool (=> (and cacba81ed_caller_has_manager_role
         (<= 0 cacba81ed_cancelled_withdrawal_amount))
    (not cacba81ed_remainder_outside_accounting)))
(define-fun report_effects () Bool (and cacba81ed_caller_has_manager_role
     (<= 0 cacba81ed_cancelled_withdrawal_amount)
     (not (not cacba81ed_remainder_outside_accounting))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
