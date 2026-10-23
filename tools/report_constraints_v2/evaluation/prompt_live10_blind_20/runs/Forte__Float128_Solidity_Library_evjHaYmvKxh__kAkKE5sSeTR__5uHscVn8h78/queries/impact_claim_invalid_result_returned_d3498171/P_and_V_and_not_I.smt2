; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca10d5770_input_is_negative () Bool)
(declare-fun ca10d5770_invalid_result_returned () Bool)
(declare-fun ca10d5770_ln_reverted () Bool)
(assert
 (= ca10d5770_input_is_negative ca10d5770_input_is_negative))
(assert
 (= ca10d5770_invalid_result_returned ca10d5770_invalid_result_returned))
(assert
 (= ca10d5770_ln_reverted ca10d5770_ln_reverted))
(define-fun report_preconditions () Bool ca10d5770_input_is_negative)
(define-fun report_safety () Bool (=> ca10d5770_input_is_negative
    (and ca10d5770_ln_reverted (not ca10d5770_invalid_result_returned))))
(define-fun report_effects () Bool (and ca10d5770_input_is_negative
     (not (and ca10d5770_ln_reverted (not ca10d5770_invalid_result_returned)))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
