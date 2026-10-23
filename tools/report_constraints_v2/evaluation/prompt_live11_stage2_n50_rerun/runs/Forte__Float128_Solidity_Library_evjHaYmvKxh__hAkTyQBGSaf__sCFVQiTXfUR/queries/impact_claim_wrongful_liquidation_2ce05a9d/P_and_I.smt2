; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c05494b90_liquidation_triggered () Bool)
(declare-fun c05494b90_pf_collateral_math_value () Int)
(declare-fun c05494b90_pf_threshold_math_value () Int)
(assert
 (= c05494b90_liquidation_triggered c05494b90_liquidation_triggered))
(assert
 (= c05494b90_pf_collateral_math_value c05494b90_pf_collateral_math_value))
(assert
 (= c05494b90_pf_threshold_math_value c05494b90_pf_threshold_math_value))
(define-fun report_preconditions () Bool (and (= 10 c05494b90_pf_threshold_math_value)
     (= 1000 c05494b90_pf_collateral_math_value)
     (> c05494b90_pf_collateral_math_value c05494b90_pf_threshold_math_value)))
(define-fun report_safety () Bool (=> (> c05494b90_pf_collateral_math_value c05494b90_pf_threshold_math_value)
    (not c05494b90_liquidation_triggered)))
(define-fun report_effects () Bool (and (> c05494b90_pf_collateral_math_value c05494b90_pf_threshold_math_value)
     (not (not c05494b90_liquidation_triggered))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
