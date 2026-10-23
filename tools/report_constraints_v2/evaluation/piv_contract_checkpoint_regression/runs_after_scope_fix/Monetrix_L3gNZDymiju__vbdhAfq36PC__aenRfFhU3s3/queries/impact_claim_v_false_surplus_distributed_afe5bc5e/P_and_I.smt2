; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ced2fe8b6_borrow_debt () Int)
(declare-fun ced2fe8b6_false_surplus_bridged () Bool)
(declare-fun ced2fe8b6_supplied_collateral () Int)
(declare-fun ced2fe8b6_usdm_supply () Int)
(assert
 (= ced2fe8b6_borrow_debt ced2fe8b6_borrow_debt))
(assert
 (= ced2fe8b6_false_surplus_bridged ced2fe8b6_false_surplus_bridged))
(assert
 (= ced2fe8b6_supplied_collateral ced2fe8b6_supplied_collateral))
(assert
 (= ced2fe8b6_usdm_supply ced2fe8b6_usdm_supply))
(define-fun report_preconditions () Bool (and (< 0 ced2fe8b6_usdm_supply)
     (< 0 ced2fe8b6_supplied_collateral)
     (< 0 ced2fe8b6_borrow_debt)))
(define-fun report_safety () Bool (=> (and (< 0 ced2fe8b6_usdm_supply)
         (< 0 ced2fe8b6_supplied_collateral)
         (< 0 ced2fe8b6_borrow_debt))
    (not ced2fe8b6_false_surplus_bridged)))
(define-fun report_effects () Bool (and (< 0 ced2fe8b6_usdm_supply)
     (< 0 ced2fe8b6_supplied_collateral)
     (< 0 ced2fe8b6_borrow_debt)
     (not (not ced2fe8b6_false_surplus_bridged))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
