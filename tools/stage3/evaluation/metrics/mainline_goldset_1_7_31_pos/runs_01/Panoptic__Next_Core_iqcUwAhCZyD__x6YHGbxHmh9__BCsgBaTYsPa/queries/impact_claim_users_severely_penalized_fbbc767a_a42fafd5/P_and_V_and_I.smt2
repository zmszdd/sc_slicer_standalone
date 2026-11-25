; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c24e21286_borrowed_eth () Int)
(declare-fun c24e21286_collateral_increases_with_credit () Bool)
(declare-fun c24e21286_credit_exceeds_loan () Bool)
(declare-fun c24e21286_lent_eth () Int)
(declare-fun c24e21286_required_collateral_after_compute () Int)
(assert
 (= c24e21286_borrowed_eth c24e21286_borrowed_eth))
(assert
 (= c24e21286_collateral_increases_with_credit c24e21286_collateral_increases_with_credit))
(assert
 (= c24e21286_credit_exceeds_loan c24e21286_credit_exceeds_loan))
(assert
 (= c24e21286_lent_eth c24e21286_lent_eth))
(assert
 (= c24e21286_required_collateral_after_compute c24e21286_required_collateral_after_compute))
(define-fun report_preconditions () Bool (and (= 100 c24e21286_borrowed_eth)
     (= 105 c24e21286_lent_eth)
     c24e21286_credit_exceeds_loan))
(define-fun report_safety () Bool (= 0 c24e21286_required_collateral_after_compute))
(define-fun report_effects () Bool (and c24e21286_credit_exceeds_loan
     (not (= 0 c24e21286_required_collateral_after_compute))
     c24e21286_collateral_increases_with_credit
     (< 0 c24e21286_required_collateral_after_compute)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
