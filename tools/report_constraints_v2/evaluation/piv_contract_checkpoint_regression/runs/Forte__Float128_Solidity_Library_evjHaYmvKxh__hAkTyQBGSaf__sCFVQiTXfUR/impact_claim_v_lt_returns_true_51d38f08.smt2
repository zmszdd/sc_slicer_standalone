; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cdc0d70aa_attacker_influences_oracle () Bool)
(declare-fun cdc0d70aa_collateral_exponent () Int)
(declare-fun cdc0d70aa_collateral_mantissa () Int)
(declare-fun cdc0d70aa_collateral_math_value () Int)
(declare-fun cdc0d70aa_lt_returns_true () Bool)
(declare-fun cdc0d70aa_threshold_exponent () Int)
(declare-fun cdc0d70aa_threshold_mantissa () Int)
(declare-fun cdc0d70aa_threshold_math_value () Int)
(assert
 (= cdc0d70aa_attacker_influences_oracle cdc0d70aa_attacker_influences_oracle))
(assert
 (= cdc0d70aa_collateral_exponent cdc0d70aa_collateral_exponent))
(assert
 (= cdc0d70aa_collateral_mantissa cdc0d70aa_collateral_mantissa))
(assert
 (= cdc0d70aa_collateral_math_value cdc0d70aa_collateral_math_value))
(assert
 (= cdc0d70aa_lt_returns_true cdc0d70aa_lt_returns_true))
(assert
 (= cdc0d70aa_threshold_exponent cdc0d70aa_threshold_exponent))
(assert
 (= cdc0d70aa_threshold_mantissa cdc0d70aa_threshold_mantissa))
(assert
 (= cdc0d70aa_threshold_math_value cdc0d70aa_threshold_math_value))
(define-fun report_preconditions () Bool (and (> cdc0d70aa_collateral_math_value cdc0d70aa_threshold_math_value)
     (= 10000000000000000000000000000000000000 cdc0d70aa_threshold_mantissa)
     (= (- 36) cdc0d70aa_threshold_exponent)
     (= 10000000000000000000000000000000000000000 cdc0d70aa_collateral_mantissa)
     (= (- 37) cdc0d70aa_collateral_exponent)
     cdc0d70aa_attacker_influences_oracle))
(define-fun report_safety () Bool (=> (> cdc0d70aa_collateral_math_value cdc0d70aa_threshold_math_value)
    (not cdc0d70aa_lt_returns_true)))
(define-fun report_effects () Bool (and (> cdc0d70aa_collateral_math_value cdc0d70aa_threshold_math_value)
     (not (not cdc0d70aa_lt_returns_true))))
