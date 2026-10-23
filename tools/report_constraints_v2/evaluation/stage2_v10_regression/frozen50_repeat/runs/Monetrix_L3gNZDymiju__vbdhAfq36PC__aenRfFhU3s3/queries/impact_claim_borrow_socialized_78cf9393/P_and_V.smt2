; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbf44e6d5_borrow_debt_present () Bool)
(declare-fun cbf44e6d5_borrow_debt_socialized_to_usdm_holders () Bool)
(declare-fun cbf44e6d5_supplied_collateral_present () Bool)
(assert
 (= cbf44e6d5_borrow_debt_present cbf44e6d5_borrow_debt_present))
(assert
 (= cbf44e6d5_borrow_debt_socialized_to_usdm_holders cbf44e6d5_borrow_debt_socialized_to_usdm_holders))
(assert
 (= cbf44e6d5_supplied_collateral_present cbf44e6d5_supplied_collateral_present))
(define-fun report_preconditions () Bool (and cbf44e6d5_borrow_debt_present cbf44e6d5_supplied_collateral_present))
(define-fun report_safety () Bool (=> (and cbf44e6d5_borrow_debt_present cbf44e6d5_supplied_collateral_present)
    (not cbf44e6d5_borrow_debt_socialized_to_usdm_holders)))
(define-fun report_effects () Bool (and cbf44e6d5_borrow_debt_present
     cbf44e6d5_supplied_collateral_present
     (not (not cbf44e6d5_borrow_debt_socialized_to_usdm_holders))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
