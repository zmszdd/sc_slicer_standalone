; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9e61c515_exponent_margin () Int)
(declare-fun c9e61c515_input_digits () Int)
(declare-fun c9e61c515_mantissa_digits () Int)
(declare-fun c9e61c515_precision_preserved () Bool)
(assert
 (= c9e61c515_exponent_margin c9e61c515_exponent_margin))
(assert
 (= c9e61c515_input_digits c9e61c515_input_digits))
(assert
 (= c9e61c515_mantissa_digits c9e61c515_mantissa_digits))
(assert
 (= c9e61c515_precision_preserved c9e61c515_precision_preserved))
(define-fun report_preconditions () Bool (and (< 38 c9e61c515_input_digits)
     (< 0 c9e61c515_exponent_margin)
     (distinct 38 c9e61c515_mantissa_digits)
     (distinct 72 c9e61c515_mantissa_digits)))
(define-fun report_safety () Bool (=> (and (< 38 c9e61c515_input_digits)
         (< 0 c9e61c515_exponent_margin)
         (distinct 38 c9e61c515_mantissa_digits)
         (distinct 72 c9e61c515_mantissa_digits))
    c9e61c515_precision_preserved))
(define-fun report_effects () Bool (and (< 38 c9e61c515_input_digits)
     (< 0 c9e61c515_exponent_margin)
     (distinct 38 c9e61c515_mantissa_digits)
     (distinct 72 c9e61c515_mantissa_digits)
     (not c9e61c515_precision_preserved)))
