; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7b22fe86_exponent_margin () Int)
(declare-fun c7b22fe86_input_digits () Int)
(declare-fun c7b22fe86_mantissa_is_38_or_72 () Bool)
(declare-fun c7b22fe86_stored_in_l_range () Bool)
(assert
 (= c7b22fe86_exponent_margin c7b22fe86_exponent_margin))
(assert
 (= c7b22fe86_input_digits c7b22fe86_input_digits))
(assert
 (= c7b22fe86_mantissa_is_38_or_72 c7b22fe86_mantissa_is_38_or_72))
(assert
 (= c7b22fe86_stored_in_l_range c7b22fe86_stored_in_l_range))
(define-fun report_preconditions () Bool (and (< 38 c7b22fe86_input_digits)
     (< 0 c7b22fe86_exponent_margin)
     (not c7b22fe86_mantissa_is_38_or_72)))
(define-fun report_safety () Bool (=> (and (< 38 c7b22fe86_input_digits)
         (> 72 c7b22fe86_input_digits)
         (< 0 c7b22fe86_exponent_margin)
         (not c7b22fe86_mantissa_is_38_or_72))
    c7b22fe86_stored_in_l_range))
(define-fun report_effects () Bool (and (< 38 c7b22fe86_input_digits)
     (> 72 c7b22fe86_input_digits)
     (< 0 c7b22fe86_exponent_margin)
     (not c7b22fe86_mantissa_is_38_or_72)
     (not c7b22fe86_stored_in_l_range)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
