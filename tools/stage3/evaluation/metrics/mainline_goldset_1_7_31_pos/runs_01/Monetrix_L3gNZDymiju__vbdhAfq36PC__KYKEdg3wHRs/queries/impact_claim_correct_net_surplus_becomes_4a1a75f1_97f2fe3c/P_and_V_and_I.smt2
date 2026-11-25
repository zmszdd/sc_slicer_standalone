; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c20debd3d_correct_net_surplus_after () Int)
(declare-fun c20debd3d_real_distributable_surplus () Int)
(declare-fun c20debd3d_settle_amount () Int)
(declare-fun c20debd3d_vault_borrow_liability_present () Bool)
(declare-fun c20debd3d_zero_amount () Int)
(assert
 (= c20debd3d_correct_net_surplus_after c20debd3d_correct_net_surplus_after))
(assert
 (= c20debd3d_real_distributable_surplus c20debd3d_real_distributable_surplus))
(assert
 (= c20debd3d_settle_amount c20debd3d_settle_amount))
(assert
 (= c20debd3d_vault_borrow_liability_present c20debd3d_vault_borrow_liability_present))
(assert
 (= c20debd3d_zero_amount c20debd3d_zero_amount))
(define-fun report_preconditions () Bool c20debd3d_vault_borrow_liability_present)
(define-fun report_safety () Bool (=> c20debd3d_vault_borrow_liability_present
    (<= c20debd3d_settle_amount c20debd3d_real_distributable_surplus)))
(define-fun report_effects () Bool (and c20debd3d_vault_borrow_liability_present
     (not (<= c20debd3d_settle_amount c20debd3d_real_distributable_surplus))
     (< c20debd3d_correct_net_surplus_after c20debd3d_zero_amount)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
