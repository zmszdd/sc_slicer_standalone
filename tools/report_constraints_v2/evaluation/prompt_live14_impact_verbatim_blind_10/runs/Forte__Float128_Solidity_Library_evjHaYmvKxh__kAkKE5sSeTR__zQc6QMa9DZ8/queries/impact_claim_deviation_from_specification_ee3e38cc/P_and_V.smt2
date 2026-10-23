; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd34d8803_deviates_from_specification () Bool)
(declare-fun cd34d8803_input_is_negative () Bool)
(declare-fun cd34d8803_input_is_zero () Bool)
(declare-fun cd34d8803_nonpositive_input_rejected () Bool)
(declare-fun cd34d8803_reference_digits () Int)
(assert
 (= cd34d8803_deviates_from_specification cd34d8803_deviates_from_specification))
(assert
 (= cd34d8803_input_is_negative cd34d8803_input_is_negative))
(assert
 (= cd34d8803_input_is_zero cd34d8803_input_is_zero))
(assert
 (= cd34d8803_nonpositive_input_rejected cd34d8803_nonpositive_input_rejected))
(assert
 (= cd34d8803_reference_digits cd34d8803_reference_digits))
(define-fun report_preconditions () Bool (and cd34d8803_input_is_negative
     cd34d8803_input_is_zero
     (< 0 cd34d8803_reference_digits)))
(define-fun report_safety () Bool (=> (or cd34d8803_input_is_negative cd34d8803_input_is_zero)
    (and cd34d8803_nonpositive_input_rejected
         (not cd34d8803_deviates_from_specification))))
(define-fun report_effects () Bool (and (or cd34d8803_input_is_negative cd34d8803_input_is_zero)
     (not (and cd34d8803_nonpositive_input_rejected
               (not cd34d8803_deviates_from_specification)))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
