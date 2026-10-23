; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4e0bc4ee_cancelled_withdrawal_amount () Int)
(declare-fun c4e0bc4ee_redelegated_amount () Int)
(assert
 (= c4e0bc4ee_cancelled_withdrawal_amount c4e0bc4ee_cancelled_withdrawal_amount))
(assert
 (= c4e0bc4ee_redelegated_amount c4e0bc4ee_redelegated_amount))
(define-fun report_preconditions () Bool (< 0 c4e0bc4ee_cancelled_withdrawal_amount))
(define-fun report_safety () Bool (=> (< 0 c4e0bc4ee_cancelled_withdrawal_amount)
    (= c4e0bc4ee_redelegated_amount c4e0bc4ee_cancelled_withdrawal_amount)))
(define-fun report_effects () Bool (and (< 0 c4e0bc4ee_cancelled_withdrawal_amount)
     (not (= c4e0bc4ee_redelegated_amount c4e0bc4ee_cancelled_withdrawal_amount))))
