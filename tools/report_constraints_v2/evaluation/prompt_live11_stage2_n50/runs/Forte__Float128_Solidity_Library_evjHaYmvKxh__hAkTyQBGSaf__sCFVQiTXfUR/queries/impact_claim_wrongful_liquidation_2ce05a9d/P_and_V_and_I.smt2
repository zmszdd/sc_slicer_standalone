; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c05494b90_collateral_exponent () Int)
(declare-fun c05494b90_collateral_math_value () Int)
(declare-fun c05494b90_liquidation_threshold_value () Int)
(declare-fun c05494b90_liquidation_triggered () Bool)
(declare-fun c05494b90_oracle_influenced_by_attacker () Bool)
(declare-fun c05494b90_threshold_exponent () Int)
(assert
 (= c05494b90_collateral_exponent c05494b90_collateral_exponent))
(assert
 (= c05494b90_collateral_math_value c05494b90_collateral_math_value))
(assert
 (= c05494b90_liquidation_threshold_value c05494b90_liquidation_threshold_value))
(assert
 (= c05494b90_liquidation_triggered c05494b90_liquidation_triggered))
(assert
 (= c05494b90_oracle_influenced_by_attacker c05494b90_oracle_influenced_by_attacker))
(assert
 (= c05494b90_threshold_exponent c05494b90_threshold_exponent))
(define-fun report_preconditions () Bool (and (> c05494b90_collateral_math_value c05494b90_liquidation_threshold_value)
     (= (- 36) c05494b90_threshold_exponent)
     (= (- 37) c05494b90_collateral_exponent)
     c05494b90_oracle_influenced_by_attacker))
(define-fun report_safety () Bool (=> (> c05494b90_collateral_math_value c05494b90_liquidation_threshold_value)
    (not c05494b90_liquidation_triggered)))
(define-fun report_effects () Bool (and (> c05494b90_collateral_math_value c05494b90_liquidation_threshold_value)
     (not (not c05494b90_liquidation_triggered))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
