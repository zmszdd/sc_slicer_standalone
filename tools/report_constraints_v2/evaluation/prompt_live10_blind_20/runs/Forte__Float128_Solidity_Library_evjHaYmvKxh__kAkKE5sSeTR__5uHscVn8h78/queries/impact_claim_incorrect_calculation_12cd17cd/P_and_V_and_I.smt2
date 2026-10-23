; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca4ca3f5e_input_is_negative () Bool)
(declare-fun ca4ca3f5e_ln_completed_without_revert () Bool)
(declare-fun ca4ca3f5e_returned_value_incorrect () Bool)
(assert
 (= ca4ca3f5e_input_is_negative ca4ca3f5e_input_is_negative))
(assert
 (= ca4ca3f5e_ln_completed_without_revert ca4ca3f5e_ln_completed_without_revert))
(assert
 (= ca4ca3f5e_returned_value_incorrect ca4ca3f5e_returned_value_incorrect))
(define-fun report_preconditions () Bool ca4ca3f5e_input_is_negative)
(define-fun report_safety () Bool (=> ca4ca3f5e_input_is_negative
    (and (not ca4ca3f5e_ln_completed_without_revert)
         (not ca4ca3f5e_returned_value_incorrect))))
(define-fun report_effects () Bool (and ca4ca3f5e_input_is_negative
     (not (and (not ca4ca3f5e_ln_completed_without_revert)
               (not ca4ca3f5e_returned_value_incorrect)))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
