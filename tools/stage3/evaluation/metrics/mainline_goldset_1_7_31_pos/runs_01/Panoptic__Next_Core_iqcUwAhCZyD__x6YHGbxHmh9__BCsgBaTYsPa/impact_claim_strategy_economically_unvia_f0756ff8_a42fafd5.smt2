; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c67baad09_collateral_reduced_by_credit () Bool)
(declare-fun c67baad09_converted_credit () Int)
(declare-fun c67baad09_credit_amount () Int)
(declare-fun c67baad09_debt_amount () Int)
(declare-fun c67baad09_required_collateral () Int)
(declare-fun c67baad09_strategy_unviable () Bool)
(assert
 (= c67baad09_collateral_reduced_by_credit c67baad09_collateral_reduced_by_credit))
(assert
 (= c67baad09_converted_credit c67baad09_converted_credit))
(assert
 (= c67baad09_credit_amount c67baad09_credit_amount))
(assert
 (= c67baad09_debt_amount c67baad09_debt_amount))
(assert
 (= c67baad09_required_collateral c67baad09_required_collateral))
(assert
 (= c67baad09_strategy_unviable c67baad09_strategy_unviable))
(define-fun report_preconditions () Bool (and (= 100 c67baad09_debt_amount)
     (= 105 c67baad09_credit_amount)
     (> c67baad09_converted_credit c67baad09_required_collateral)))
(define-fun report_safety () Bool (=> (> c67baad09_converted_credit c67baad09_required_collateral)
    c67baad09_collateral_reduced_by_credit))
(define-fun report_effects () Bool (and (> c67baad09_converted_credit c67baad09_required_collateral)
     (not c67baad09_collateral_reduced_by_credit)
     c67baad09_strategy_unviable))
