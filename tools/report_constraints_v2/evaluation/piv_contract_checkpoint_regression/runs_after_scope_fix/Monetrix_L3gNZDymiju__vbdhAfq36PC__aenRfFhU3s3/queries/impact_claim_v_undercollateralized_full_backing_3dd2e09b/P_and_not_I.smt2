; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c43d0ae57_borrow_debt () Int)
(declare-fun c43d0ae57_net_backing () Int)
(declare-fun c43d0ae57_reported_backing () Int)
(declare-fun c43d0ae57_supplied_collateral () Int)
(declare-fun c43d0ae57_usdm_supply () Int)
(assert
 (= c43d0ae57_borrow_debt c43d0ae57_borrow_debt))
(assert
 (= c43d0ae57_net_backing c43d0ae57_net_backing))
(assert
 (= c43d0ae57_reported_backing c43d0ae57_reported_backing))
(assert
 (= c43d0ae57_supplied_collateral c43d0ae57_supplied_collateral))
(assert
 (= c43d0ae57_usdm_supply c43d0ae57_usdm_supply))
(define-fun report_preconditions () Bool (and (< 0 c43d0ae57_usdm_supply)
     (< 0 c43d0ae57_supplied_collateral)
     (< 0 c43d0ae57_borrow_debt)))
(define-fun report_safety () Bool (=> (= c43d0ae57_net_backing
       (- c43d0ae57_supplied_collateral c43d0ae57_borrow_debt))
    (=> (and (< 0 c43d0ae57_usdm_supply)
             (< 0 c43d0ae57_supplied_collateral)
             (< 0 c43d0ae57_borrow_debt))
        (<= c43d0ae57_reported_backing c43d0ae57_net_backing))))
(define-fun report_effects () Bool (and (= c43d0ae57_net_backing
        (- c43d0ae57_supplied_collateral c43d0ae57_borrow_debt))
     (< 0 c43d0ae57_usdm_supply)
     (< 0 c43d0ae57_supplied_collateral)
     (< 0 c43d0ae57_borrow_debt)
     (not (<= c43d0ae57_reported_backing c43d0ae57_net_backing))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
