; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c77cfb3c4_cancelled_withdrawal_amount () Int)
(declare-fun c77cfb3c4_manager_has_role () Bool)
(declare-fun c77cfb3c4_redelegated_amount () Int)
(declare-fun c77cfb3c4_remainder_nonzero () Bool)
(assert
 (= c77cfb3c4_cancelled_withdrawal_amount c77cfb3c4_cancelled_withdrawal_amount))
(assert
 (= c77cfb3c4_manager_has_role c77cfb3c4_manager_has_role))
(assert
 (= c77cfb3c4_redelegated_amount c77cfb3c4_redelegated_amount))
(assert
 (= c77cfb3c4_remainder_nonzero c77cfb3c4_remainder_nonzero))
(define-fun report_preconditions () Bool (and (< 0 c77cfb3c4_cancelled_withdrawal_amount)
     c77cfb3c4_manager_has_role
     c77cfb3c4_remainder_nonzero))
(define-fun report_safety () Bool (=> (and c77cfb3c4_manager_has_role c77cfb3c4_remainder_nonzero)
    (= c77cfb3c4_redelegated_amount c77cfb3c4_cancelled_withdrawal_amount)))
(define-fun report_effects () Bool (and c77cfb3c4_manager_has_role
     c77cfb3c4_remainder_nonzero
     (not (= c77cfb3c4_redelegated_amount c77cfb3c4_cancelled_withdrawal_amount))))
