; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd66ecfbe_borrowed_debt_amount () Int)
(declare-fun cd66ecfbe_computed_collateral_requirement () Int)
(declare-fun cd66ecfbe_converted_credit () Int)
(declare-fun cd66ecfbe_lent_credit_amount () Int)
(declare-fun cd66ecfbe_required_collateral_for_debt () Int)
(assert
 (= cd66ecfbe_borrowed_debt_amount cd66ecfbe_borrowed_debt_amount))
(assert
 (= cd66ecfbe_computed_collateral_requirement cd66ecfbe_computed_collateral_requirement))
(assert
 (= cd66ecfbe_converted_credit cd66ecfbe_converted_credit))
(assert
 (= cd66ecfbe_lent_credit_amount cd66ecfbe_lent_credit_amount))
(assert
 (= cd66ecfbe_required_collateral_for_debt cd66ecfbe_required_collateral_for_debt))
(define-fun report_preconditions () Bool (and (= 100 cd66ecfbe_borrowed_debt_amount)
     (= 105 cd66ecfbe_lent_credit_amount)
     (= 105 cd66ecfbe_converted_credit)
     (= 100 cd66ecfbe_required_collateral_for_debt)
     (> cd66ecfbe_converted_credit cd66ecfbe_required_collateral_for_debt)))
(define-fun report_safety () Bool (=> (> cd66ecfbe_converted_credit cd66ecfbe_required_collateral_for_debt)
    (< cd66ecfbe_computed_collateral_requirement
       cd66ecfbe_required_collateral_for_debt)))
(define-fun report_effects () Bool (and (> cd66ecfbe_converted_credit cd66ecfbe_required_collateral_for_debt)
     (not (< cd66ecfbe_computed_collateral_requirement
             cd66ecfbe_required_collateral_for_debt))
     (> cd66ecfbe_computed_collateral_requirement
        cd66ecfbe_required_collateral_for_debt)
     (= cd66ecfbe_computed_collateral_requirement cd66ecfbe_converted_credit)))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
