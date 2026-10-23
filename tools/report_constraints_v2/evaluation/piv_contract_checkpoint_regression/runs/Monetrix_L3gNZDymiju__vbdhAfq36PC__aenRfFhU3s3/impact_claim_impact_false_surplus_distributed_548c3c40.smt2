; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7478ee01_false_surplus_distributed () Bool)
(declare-fun c7478ee01_principal_bridged () Int)
(declare-fun c7478ee01_usdc_borrow_debt_amount () Int)
(declare-fun c7478ee01_usdc_deposited () Int)
(assert
 (= c7478ee01_false_surplus_distributed c7478ee01_false_surplus_distributed))
(assert
 (= c7478ee01_principal_bridged c7478ee01_principal_bridged))
(assert
 (= c7478ee01_usdc_borrow_debt_amount c7478ee01_usdc_borrow_debt_amount))
(assert
 (= c7478ee01_usdc_deposited c7478ee01_usdc_deposited))
(define-fun report_preconditions () Bool (and (< 0 c7478ee01_usdc_deposited)
     (< 0 c7478ee01_principal_bridged)
     (< 0 c7478ee01_usdc_borrow_debt_amount)))
(define-fun report_safety () Bool (=> (and (< 0 c7478ee01_usdc_deposited)
         (< 0 c7478ee01_principal_bridged)
         (< 0 c7478ee01_usdc_borrow_debt_amount))
    (not c7478ee01_false_surplus_distributed)))
(define-fun report_effects () Bool (and (< 0 c7478ee01_usdc_deposited)
     (< 0 c7478ee01_principal_bridged)
     (< 0 c7478ee01_usdc_borrow_debt_amount)
     (not (not c7478ee01_false_surplus_distributed))))
