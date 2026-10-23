; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c87dee6f5_collateral_exponent () Int)
(declare-fun c87dee6f5_collateral_mantissa () Int)
(declare-fun c87dee6f5_collateral_math_value () Int)
(declare-fun c87dee6f5_liquidation_triggered () Bool)
(declare-fun c87dee6f5_packedfloat_is_uint256_alias () Bool)
(declare-fun c87dee6f5_threshold_exponent () Int)
(declare-fun c87dee6f5_threshold_mantissa () Int)
(declare-fun c87dee6f5_threshold_math_value () Int)
(assert
 (= c87dee6f5_collateral_exponent c87dee6f5_collateral_exponent))
(assert
 (= c87dee6f5_collateral_mantissa c87dee6f5_collateral_mantissa))
(assert
 (= c87dee6f5_collateral_math_value c87dee6f5_collateral_math_value))
(assert
 (= c87dee6f5_liquidation_triggered c87dee6f5_liquidation_triggered))
(assert
 (= c87dee6f5_packedfloat_is_uint256_alias c87dee6f5_packedfloat_is_uint256_alias))
(assert
 (= c87dee6f5_threshold_exponent c87dee6f5_threshold_exponent))
(assert
 (= c87dee6f5_threshold_mantissa c87dee6f5_threshold_mantissa))
(assert
 (= c87dee6f5_threshold_math_value c87dee6f5_threshold_math_value))
(define-fun report_preconditions () Bool (and (> c87dee6f5_collateral_math_value c87dee6f5_threshold_math_value)
     (= 10000000000000000000000000000000000000 c87dee6f5_threshold_mantissa)
     (= (- 36) c87dee6f5_threshold_exponent)
     (= 10000000000000000000000000000000000000000 c87dee6f5_collateral_mantissa)
     (= (- 37) c87dee6f5_collateral_exponent)
     c87dee6f5_packedfloat_is_uint256_alias))
(define-fun report_safety () Bool (=> (and (> c87dee6f5_collateral_math_value c87dee6f5_threshold_math_value)
         c87dee6f5_packedfloat_is_uint256_alias)
    (not c87dee6f5_liquidation_triggered)))
(define-fun report_effects () Bool (and (> c87dee6f5_collateral_math_value c87dee6f5_threshold_math_value)
     c87dee6f5_packedfloat_is_uint256_alias
     (not (not c87dee6f5_liquidation_triggered))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
