; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2decb4b9_borrow_liability_present () Bool)
(declare-fun c2decb4b9_real_distributable_surplus () Int)
(declare-fun c2decb4b9_settle_amount () Int)
(declare-fun c2decb4b9_settlement_breaks_invariants () Bool)
(assert
 (= c2decb4b9_borrow_liability_present c2decb4b9_borrow_liability_present))
(assert
 (= c2decb4b9_real_distributable_surplus c2decb4b9_real_distributable_surplus))
(assert
 (= c2decb4b9_settle_amount c2decb4b9_settle_amount))
(assert
 (= c2decb4b9_settlement_breaks_invariants c2decb4b9_settlement_breaks_invariants))
(define-fun report_preconditions () Bool c2decb4b9_borrow_liability_present)
(define-fun report_safety () Bool (=> c2decb4b9_borrow_liability_present
    (<= c2decb4b9_settle_amount c2decb4b9_real_distributable_surplus)))
(define-fun report_effects () Bool (and c2decb4b9_borrow_liability_present
     (not (<= c2decb4b9_settle_amount c2decb4b9_real_distributable_surplus))
     c2decb4b9_settlement_breaks_invariants))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
