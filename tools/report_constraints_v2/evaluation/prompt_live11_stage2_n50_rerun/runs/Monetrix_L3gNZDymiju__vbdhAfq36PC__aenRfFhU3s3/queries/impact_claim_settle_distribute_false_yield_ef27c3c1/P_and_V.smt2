; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c79d39053_borrow_debt () Int)
(declare-fun c79d39053_distributed_as_yield () Int)
(declare-fun c79d39053_real_surplus () Int)
(declare-fun c79d39053_supplied_collateral () Int)
(assert
 (= c79d39053_borrow_debt c79d39053_borrow_debt))
(assert
 (= c79d39053_distributed_as_yield c79d39053_distributed_as_yield))
(assert
 (= c79d39053_real_surplus c79d39053_real_surplus))
(assert
 (= c79d39053_supplied_collateral c79d39053_supplied_collateral))
(define-fun report_preconditions () Bool (and (< 0 c79d39053_borrow_debt) (< 0 c79d39053_supplied_collateral)))
(define-fun report_safety () Bool (=> (= c79d39053_real_surplus
       (- c79d39053_supplied_collateral c79d39053_borrow_debt))
    (=> (and (< 0 c79d39053_borrow_debt) (< 0 c79d39053_supplied_collateral))
        (<= c79d39053_distributed_as_yield c79d39053_real_surplus))))
(define-fun report_effects () Bool (and (= c79d39053_real_surplus
        (- c79d39053_supplied_collateral c79d39053_borrow_debt))
     (< 0 c79d39053_borrow_debt)
     (< 0 c79d39053_supplied_collateral)
     (not (<= c79d39053_distributed_as_yield c79d39053_real_surplus))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
