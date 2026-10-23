; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c73238d01_caller_is_owner () Bool)
(declare-fun c73238d01_held_duration_exceeds_deadline () Bool)
(assert
 (= c73238d01_caller_is_owner c73238d01_caller_is_owner))
(assert
 (= c73238d01_held_duration_exceeds_deadline c73238d01_held_duration_exceeds_deadline))
(define-fun report_preconditions () Bool c73238d01_caller_is_owner)
(define-fun report_safety () Bool (=> c73238d01_caller_is_owner (not c73238d01_held_duration_exceeds_deadline)))
(define-fun report_effects () Bool (and c73238d01_caller_is_owner
     (not (not c73238d01_held_duration_exceeds_deadline))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
