; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun creator_internal_balance () Int)
(declare-fun campaign_amount () Int)
(declare-fun operator_authorized () Bool)
(declare-fun operator_allowance () Int)
(declare-fun operator_charged () Bool)
(assert
 (= creator_internal_balance creator_internal_balance))
(assert
 (= campaign_amount campaign_amount))
(assert
 (= operator_authorized operator_authorized))
(assert
 (= operator_allowance operator_allowance))
(assert
 (= operator_charged operator_charged))
(define-fun report_preconditions () Bool (and (>= creator_internal_balance campaign_amount)
     operator_authorized
     (>= operator_allowance campaign_amount)
     (= 1000 campaign_amount)))
(define-fun report_safety () Bool (=> (and operator_authorized
         (>= creator_internal_balance campaign_amount)
         (>= operator_allowance campaign_amount))
    (not operator_charged)))
(define-fun report_effects () Bool (and operator_authorized
     (>= creator_internal_balance campaign_amount)
     (>= operator_allowance campaign_amount)
     (not (not operator_charged))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
