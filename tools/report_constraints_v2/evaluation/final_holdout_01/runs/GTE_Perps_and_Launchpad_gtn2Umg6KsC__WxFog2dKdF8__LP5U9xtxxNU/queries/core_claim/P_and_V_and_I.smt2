; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun pair_already_exists () Bool)
(declare-fun graduation_completed () Bool)
(assert
 (= pair_already_exists pair_already_exists))
(assert
 (= graduation_completed graduation_completed))
(define-fun report_preconditions () Bool (and pair_already_exists pair_already_exists))
(define-fun report_safety () Bool (=> pair_already_exists graduation_completed))
(define-fun report_effects () Bool (and pair_already_exists (not graduation_completed)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
