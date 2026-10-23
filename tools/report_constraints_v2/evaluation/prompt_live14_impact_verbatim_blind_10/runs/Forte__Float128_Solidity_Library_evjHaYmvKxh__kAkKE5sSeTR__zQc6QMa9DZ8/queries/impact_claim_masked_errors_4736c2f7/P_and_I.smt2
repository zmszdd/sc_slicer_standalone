; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cedb825bd_input_is_negative () Bool)
(declare-fun cedb825bd_input_is_zero () Bool)
(declare-fun cedb825bd_reference_digits () Int)
(declare-fun cedb825bd_revert_occurred () Bool)
(assert
 (= cedb825bd_input_is_negative cedb825bd_input_is_negative))
(assert
 (= cedb825bd_input_is_zero cedb825bd_input_is_zero))
(assert
 (= cedb825bd_reference_digits cedb825bd_reference_digits))
(assert
 (= cedb825bd_revert_occurred cedb825bd_revert_occurred))
(define-fun report_preconditions () Bool (and cedb825bd_input_is_negative
     cedb825bd_input_is_zero
     (< 0 cedb825bd_reference_digits)))
(define-fun report_safety () Bool (=> (or cedb825bd_input_is_negative cedb825bd_input_is_zero)
    cedb825bd_revert_occurred))
(define-fun report_effects () Bool (and (or cedb825bd_input_is_negative cedb825bd_input_is_zero)
     (not cedb825bd_revert_occurred)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
