; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun creator_internal_balance () Int)
(declare-fun campaign_amount () Int)
(declare-fun operator_paid_amount () Int)
(declare-fun creator_funded_amount () Int)
(assert
 (= creator_internal_balance creator_internal_balance))
(assert
 (= campaign_amount campaign_amount))
(assert
 (= operator_paid_amount operator_paid_amount))
(assert
 (= creator_funded_amount creator_funded_amount))
(define-fun report_preconditions () Bool (and (>= creator_internal_balance campaign_amount)
     (= 1000 campaign_amount)
     (= 1000 campaign_amount)))
(define-fun report_safety () Bool (=> (>= creator_internal_balance campaign_amount)
    (and (= 0 operator_paid_amount) (= creator_funded_amount campaign_amount))))
(define-fun report_effects () Bool (and (>= creator_internal_balance campaign_amount)
     (not (and (= 0 operator_paid_amount)
               (= creator_funded_amount campaign_amount)))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
