; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun unclaimed_bribes_present () Bool)
(declare-fun voted_from_false () Bool)
(declare-fun claim_succeeds () Bool)
(assert
 (= unclaimed_bribes_present unclaimed_bribes_present))
(assert
 (= voted_from_false voted_from_false))
(assert
 (= claim_succeeds claim_succeeds))
(define-fun report_preconditions () Bool (and unclaimed_bribes_present voted_from_false))
(define-fun report_safety () Bool (=> (and unclaimed_bribes_present voted_from_false) claim_succeeds))
(define-fun report_effects () Bool (and unclaimed_bribes_present voted_from_false (not claim_succeeds)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
