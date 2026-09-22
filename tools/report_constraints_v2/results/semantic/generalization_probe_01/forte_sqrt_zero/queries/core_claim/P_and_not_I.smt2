; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun can_reach_sqrt () Bool)
(declare-fun input_is_zero () Bool)
(declare-fun returns_valid_zero () Bool)
(assert
 (= can_reach_sqrt can_reach_sqrt))
(assert
 (= input_is_zero input_is_zero))
(assert
 (= returns_valid_zero returns_valid_zero))
(define-fun report_preconditions () Bool (and can_reach_sqrt input_is_zero))
(define-fun report_safety () Bool (=> input_is_zero returns_valid_zero))
(define-fun report_effects () Bool (and input_is_zero (not returns_valid_zero)))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
