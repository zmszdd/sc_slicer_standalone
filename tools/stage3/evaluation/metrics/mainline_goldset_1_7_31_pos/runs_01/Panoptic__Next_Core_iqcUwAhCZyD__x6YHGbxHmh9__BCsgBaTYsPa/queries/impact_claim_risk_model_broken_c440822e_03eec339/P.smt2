; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca16f2d93_credit_amount () Int)
(declare-fun ca16f2d93_debt_amount () Int)
(declare-fun ca16f2d93_near_zero_collateral_bound () Int)
(declare-fun ca16f2d93_required_collateral_amount () Int)
(declare-fun ca16f2d93_risk_model_broken_flag () Bool)
(assert
 (= ca16f2d93_credit_amount ca16f2d93_credit_amount))
(assert
 (= ca16f2d93_debt_amount ca16f2d93_debt_amount))
(assert
 (= ca16f2d93_near_zero_collateral_bound ca16f2d93_near_zero_collateral_bound))
(assert
 (= ca16f2d93_required_collateral_amount ca16f2d93_required_collateral_amount))
(assert
 (= ca16f2d93_risk_model_broken_flag ca16f2d93_risk_model_broken_flag))
(define-fun report_preconditions () Bool (and (= 100 ca16f2d93_debt_amount)
     (= 105 ca16f2d93_credit_amount)
     (> ca16f2d93_credit_amount ca16f2d93_debt_amount)))
(define-fun report_safety () Bool (=> (>= ca16f2d93_credit_amount ca16f2d93_debt_amount)
    (<= ca16f2d93_required_collateral_amount
        ca16f2d93_near_zero_collateral_bound)))
(define-fun report_effects () Bool (and (>= ca16f2d93_credit_amount ca16f2d93_debt_amount)
     (not (<= ca16f2d93_required_collateral_amount
              ca16f2d93_near_zero_collateral_bound))
     ca16f2d93_risk_model_broken_flag))
(assert report_preconditions)
(check-sat)
(get-model)
