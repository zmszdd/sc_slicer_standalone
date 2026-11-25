; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2ecb9198_converted_credit () Int)
(declare-fun c2ecb9198_debt_required_collateral () Int)
(declare-fun c2ecb9198_near_zero_collateral_bound () Int)
(declare-fun c2ecb9198_required_collateral_after_compute () Int)
(assert
 (= c2ecb9198_converted_credit c2ecb9198_converted_credit))
(assert
 (= c2ecb9198_debt_required_collateral c2ecb9198_debt_required_collateral))
(assert
 (= c2ecb9198_near_zero_collateral_bound c2ecb9198_near_zero_collateral_bound))
(assert
 (= c2ecb9198_required_collateral_after_compute c2ecb9198_required_collateral_after_compute))
(define-fun report_preconditions () Bool (and (= 100 c2ecb9198_debt_required_collateral)
     (= 105 c2ecb9198_converted_credit)
     (> c2ecb9198_converted_credit c2ecb9198_debt_required_collateral)))
(define-fun report_safety () Bool (=> (>= c2ecb9198_converted_credit c2ecb9198_debt_required_collateral)
    (<= c2ecb9198_required_collateral_after_compute
        c2ecb9198_near_zero_collateral_bound)))
(define-fun report_effects () Bool (and (>= c2ecb9198_converted_credit c2ecb9198_debt_required_collateral)
     (not (<= c2ecb9198_required_collateral_after_compute
              c2ecb9198_near_zero_collateral_bound))
     (> c2ecb9198_required_collateral_after_compute
        c2ecb9198_near_zero_collateral_bound)
     (> c2ecb9198_required_collateral_after_compute
        c2ecb9198_near_zero_collateral_bound)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
