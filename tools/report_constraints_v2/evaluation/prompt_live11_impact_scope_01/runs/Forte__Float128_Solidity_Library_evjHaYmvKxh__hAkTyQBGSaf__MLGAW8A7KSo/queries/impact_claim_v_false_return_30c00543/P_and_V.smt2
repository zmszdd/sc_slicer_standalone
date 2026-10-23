; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbae5f594_float_a_has_l_mantissa () Bool)
(declare-fun cbae5f594_float_a_is_negative () Bool)
(declare-fun cbae5f594_float_b_has_l_mantissa () Bool)
(declare-fun cbae5f594_float_b_is_negative () Bool)
(declare-fun cbae5f594_floats_inherently_equal () Bool)
(declare-fun cbae5f594_le_returned_false () Bool)
(assert
 (= cbae5f594_float_a_has_l_mantissa cbae5f594_float_a_has_l_mantissa))
(assert
 (= cbae5f594_float_a_is_negative cbae5f594_float_a_is_negative))
(assert
 (= cbae5f594_float_b_has_l_mantissa cbae5f594_float_b_has_l_mantissa))
(assert
 (= cbae5f594_float_b_is_negative cbae5f594_float_b_is_negative))
(assert
 (= cbae5f594_floats_inherently_equal cbae5f594_floats_inherently_equal))
(assert
 (= cbae5f594_le_returned_false cbae5f594_le_returned_false))
(define-fun report_preconditions () Bool (and cbae5f594_float_a_is_negative
     cbae5f594_float_b_is_negative
     (or cbae5f594_float_a_has_l_mantissa cbae5f594_float_b_has_l_mantissa)
     cbae5f594_floats_inherently_equal))
(define-fun report_safety () Bool (=> (and cbae5f594_float_a_is_negative
         cbae5f594_float_b_is_negative
         (or cbae5f594_float_a_has_l_mantissa cbae5f594_float_b_has_l_mantissa)
         cbae5f594_floats_inherently_equal)
    (not cbae5f594_le_returned_false)))
(define-fun report_effects () Bool (and cbae5f594_float_a_is_negative
     cbae5f594_float_b_is_negative
     (or cbae5f594_float_a_has_l_mantissa cbae5f594_float_b_has_l_mantissa)
     cbae5f594_floats_inherently_equal
     (not (not cbae5f594_le_returned_false))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
