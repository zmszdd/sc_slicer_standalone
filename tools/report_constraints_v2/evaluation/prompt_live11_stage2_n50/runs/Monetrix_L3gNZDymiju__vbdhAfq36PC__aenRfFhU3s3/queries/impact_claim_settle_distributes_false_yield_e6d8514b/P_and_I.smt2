; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0ecae508_principal_bridged () Int)
(declare-fun c0ecae508_settle_distributed_as_yield () Bool)
(declare-fun c0ecae508_usdc_borrow_debt_amount () Int)
(declare-fun c0ecae508_usdc_deposited () Int)
(assert
 (= c0ecae508_principal_bridged c0ecae508_principal_bridged))
(assert
 (= c0ecae508_settle_distributed_as_yield c0ecae508_settle_distributed_as_yield))
(assert
 (= c0ecae508_usdc_borrow_debt_amount c0ecae508_usdc_borrow_debt_amount))
(assert
 (= c0ecae508_usdc_deposited c0ecae508_usdc_deposited))
(define-fun report_preconditions () Bool (and (< 0 c0ecae508_usdc_deposited)
     (< 0 c0ecae508_principal_bridged)
     (< 0 c0ecae508_usdc_borrow_debt_amount)))
(define-fun report_safety () Bool (=> (and (< 0 c0ecae508_usdc_deposited)
         (< 0 c0ecae508_principal_bridged)
         (< 0 c0ecae508_usdc_borrow_debt_amount))
    (not c0ecae508_settle_distributed_as_yield)))
(define-fun report_effects () Bool (and (< 0 c0ecae508_usdc_deposited)
     (< 0 c0ecae508_principal_bridged)
     (< 0 c0ecae508_usdc_borrow_debt_amount)
     (not (not c0ecae508_settle_distributed_as_yield))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
