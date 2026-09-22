; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun input_a () Int)
(declare-fun halt_no_data () Bool)
(assert
 (= input_a input_a))
(assert
 (= halt_no_data halt_no_data))
(define-fun report_preconditions () Bool (= 0 input_a))
(define-fun report_safety () Bool (=> (= 0 input_a) (not halt_no_data)))
(define-fun report_effects () Bool (and (= 0 input_a) halt_no_data))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
