; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c36a6f307_caller_is_owner () Bool)
(declare-fun c36a6f307_deadline_enforced () Bool)
(assert
 (= c36a6f307_caller_is_owner c36a6f307_caller_is_owner))
(assert
 (= c36a6f307_deadline_enforced c36a6f307_deadline_enforced))
(define-fun report_preconditions () Bool c36a6f307_caller_is_owner)
(define-fun report_safety () Bool (=> c36a6f307_caller_is_owner c36a6f307_deadline_enforced))
(define-fun report_effects () Bool (and c36a6f307_caller_is_owner (not c36a6f307_deadline_enforced)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
