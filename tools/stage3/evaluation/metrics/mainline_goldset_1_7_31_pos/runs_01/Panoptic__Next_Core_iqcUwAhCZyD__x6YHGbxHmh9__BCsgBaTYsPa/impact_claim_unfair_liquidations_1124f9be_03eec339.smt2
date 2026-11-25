; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cf96856bf_converted_credit () Int)
(declare-fun cf96856bf_near_zero_collateral_bound () Int)
(declare-fun cf96856bf_required_collateral () Int)
(declare-fun cf96856bf_unfair_liquidation_risk () Bool)
(assert
 (= cf96856bf_converted_credit cf96856bf_converted_credit))
(assert
 (= cf96856bf_near_zero_collateral_bound cf96856bf_near_zero_collateral_bound))
(assert
 (= cf96856bf_required_collateral cf96856bf_required_collateral))
(assert
 (= cf96856bf_unfair_liquidation_risk cf96856bf_unfair_liquidation_risk))
(define-fun report_preconditions () Bool (and (= 105 cf96856bf_converted_credit)
     (= 100 cf96856bf_required_collateral)
     (> cf96856bf_converted_credit cf96856bf_required_collateral)))
(define-fun report_safety () Bool (=> (>= cf96856bf_converted_credit cf96856bf_required_collateral)
    (<= cf96856bf_required_collateral cf96856bf_near_zero_collateral_bound)))
(define-fun report_effects () Bool (and (>= cf96856bf_converted_credit cf96856bf_required_collateral)
     (not (<= cf96856bf_required_collateral
              cf96856bf_near_zero_collateral_bound))
     cf96856bf_unfair_liquidation_risk
     cf96856bf_unfair_liquidation_risk))
