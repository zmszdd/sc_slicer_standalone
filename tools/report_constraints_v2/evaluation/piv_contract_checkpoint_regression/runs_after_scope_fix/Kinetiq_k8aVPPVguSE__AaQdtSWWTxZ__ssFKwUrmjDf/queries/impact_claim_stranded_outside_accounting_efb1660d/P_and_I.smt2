; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8417db82_accounted_amount () Int)
(declare-fun c8417db82_cancelled_withdrawal_amount () Int)
(declare-fun c8417db82_redelegation_occurred () Bool)
(assert
 (= c8417db82_accounted_amount c8417db82_accounted_amount))
(assert
 (= c8417db82_cancelled_withdrawal_amount c8417db82_cancelled_withdrawal_amount))
(assert
 (= c8417db82_redelegation_occurred c8417db82_redelegation_occurred))
(define-fun report_preconditions () Bool (< 0 c8417db82_cancelled_withdrawal_amount))
(define-fun report_safety () Bool (=> c8417db82_redelegation_occurred
    (= c8417db82_accounted_amount c8417db82_cancelled_withdrawal_amount)))
(define-fun report_effects () Bool (and c8417db82_redelegation_occurred
     (not (= c8417db82_accounted_amount c8417db82_cancelled_withdrawal_amount))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
