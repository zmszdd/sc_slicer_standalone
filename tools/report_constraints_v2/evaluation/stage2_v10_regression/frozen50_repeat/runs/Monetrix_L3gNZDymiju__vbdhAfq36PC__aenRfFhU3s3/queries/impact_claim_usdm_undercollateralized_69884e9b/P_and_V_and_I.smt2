; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4dc1f977_borrow_debt_present () Bool)
(declare-fun c4dc1f977_reported_backing_nets_borrow () Bool)
(declare-fun c4dc1f977_supplied_collateral_present () Bool)
(declare-fun c4dc1f977_usdm_undercollateralized () Bool)
(assert
 (= c4dc1f977_borrow_debt_present c4dc1f977_borrow_debt_present))
(assert
 (= c4dc1f977_reported_backing_nets_borrow c4dc1f977_reported_backing_nets_borrow))
(assert
 (= c4dc1f977_supplied_collateral_present c4dc1f977_supplied_collateral_present))
(assert
 (= c4dc1f977_usdm_undercollateralized c4dc1f977_usdm_undercollateralized))
(define-fun report_preconditions () Bool (and c4dc1f977_borrow_debt_present c4dc1f977_supplied_collateral_present))
(define-fun report_safety () Bool (=> (and c4dc1f977_borrow_debt_present c4dc1f977_supplied_collateral_present)
    (and c4dc1f977_reported_backing_nets_borrow
         (not c4dc1f977_usdm_undercollateralized))))
(define-fun report_effects () Bool (and c4dc1f977_borrow_debt_present
     c4dc1f977_supplied_collateral_present
     (not (and c4dc1f977_reported_backing_nets_borrow
               (not c4dc1f977_usdm_undercollateralized)))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
