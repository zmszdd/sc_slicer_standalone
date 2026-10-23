; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4dc1f977_borrow_debt () Int)
(declare-fun c4dc1f977_reported_backing () Int)
(declare-fun c4dc1f977_supplied_collateral () Int)
(declare-fun c4dc1f977_usdm_fully_backed () Bool)
(assert
 (= c4dc1f977_borrow_debt c4dc1f977_borrow_debt))
(assert
 (= c4dc1f977_reported_backing c4dc1f977_reported_backing))
(assert
 (= c4dc1f977_supplied_collateral c4dc1f977_supplied_collateral))
(assert
 (= c4dc1f977_usdm_fully_backed c4dc1f977_usdm_fully_backed))
(define-fun report_preconditions () Bool (and (< 0 c4dc1f977_borrow_debt) (< 0 c4dc1f977_supplied_collateral)))
(define-fun report_safety () Bool (=> (and (< 0 c4dc1f977_borrow_debt) (< 0 c4dc1f977_supplied_collateral))
    (and (<= c4dc1f977_reported_backing c4dc1f977_supplied_collateral)
         c4dc1f977_usdm_fully_backed)))
(define-fun report_effects () Bool (and (< 0 c4dc1f977_borrow_debt)
     (< 0 c4dc1f977_supplied_collateral)
     (not (and (<= c4dc1f977_reported_backing c4dc1f977_supplied_collateral)
               c4dc1f977_usdm_fully_backed))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
