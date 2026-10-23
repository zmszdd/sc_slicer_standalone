; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4516a9a7_graduation_completed () Bool)
(declare-fun c4516a9a7_graduation_reverted () Bool)
(declare-fun c4516a9a7_pair_deployed_before_graduation () Bool)
(declare-fun c4516a9a7_token_near_graduation () Bool)
(assert
 (= c4516a9a7_graduation_completed c4516a9a7_graduation_completed))
(assert
 (= c4516a9a7_graduation_reverted c4516a9a7_graduation_reverted))
(assert
 (= c4516a9a7_pair_deployed_before_graduation c4516a9a7_pair_deployed_before_graduation))
(assert
 (= c4516a9a7_token_near_graduation c4516a9a7_token_near_graduation))
(define-fun report_preconditions () Bool (and c4516a9a7_token_near_graduation c4516a9a7_pair_deployed_before_graduation))
(define-fun report_safety () Bool (=> (and c4516a9a7_token_near_graduation
         c4516a9a7_pair_deployed_before_graduation)
    (and c4516a9a7_graduation_completed (not c4516a9a7_graduation_reverted))))
(define-fun report_effects () Bool (and c4516a9a7_token_near_graduation
     c4516a9a7_pair_deployed_before_graduation
     (not (and c4516a9a7_graduation_completed
               (not c4516a9a7_graduation_reverted)))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
