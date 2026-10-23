; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c47419536_collateral_math_value () Int)
(declare-fun c47419536_collateral_raw_exponent () Int)
(declare-fun c47419536_lt_returns_true () Bool)
(declare-fun c47419536_threshold_math_value () Int)
(declare-fun c47419536_threshold_raw_exponent () Int)
(declare-fun c47419536_unnormalized_wrap_allowed () Bool)
(assert
 (= c47419536_collateral_math_value c47419536_collateral_math_value))
(assert
 (= c47419536_collateral_raw_exponent c47419536_collateral_raw_exponent))
(assert
 (= c47419536_lt_returns_true c47419536_lt_returns_true))
(assert
 (= c47419536_threshold_math_value c47419536_threshold_math_value))
(assert
 (= c47419536_threshold_raw_exponent c47419536_threshold_raw_exponent))
(assert
 (= c47419536_unnormalized_wrap_allowed c47419536_unnormalized_wrap_allowed))
(define-fun report_preconditions () Bool (and (> c47419536_collateral_math_value c47419536_threshold_math_value)
     (= (- 36) c47419536_threshold_raw_exponent)
     (= (- 37) c47419536_collateral_raw_exponent)
     c47419536_unnormalized_wrap_allowed))
(define-fun report_safety () Bool (=> (and (> c47419536_collateral_math_value c47419536_threshold_math_value)
         (= (- 37) c47419536_collateral_raw_exponent)
         (= (- 36) c47419536_threshold_raw_exponent))
    (not c47419536_lt_returns_true)))
(define-fun report_effects () Bool (and (> c47419536_collateral_math_value c47419536_threshold_math_value)
     (= (- 37) c47419536_collateral_raw_exponent)
     (= (- 36) c47419536_threshold_raw_exponent)
     (not (not c47419536_lt_returns_true))))
(assert report_preconditions)
(check-sat)
(get-model)
