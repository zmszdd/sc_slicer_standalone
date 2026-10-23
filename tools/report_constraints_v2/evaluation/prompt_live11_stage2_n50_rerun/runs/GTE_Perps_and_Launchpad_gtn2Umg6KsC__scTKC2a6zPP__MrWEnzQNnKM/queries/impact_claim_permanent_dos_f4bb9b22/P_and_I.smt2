; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c791a6aab_graduation_completes () Bool)
(declare-fun c791a6aab_graduation_permanently_disabled () Bool)
(declare-fun c791a6aab_pair_deployed_before_graduation () Bool)
(declare-fun c791a6aab_token_near_graduation () Bool)
(assert
 (= c791a6aab_graduation_completes c791a6aab_graduation_completes))
(assert
 (= c791a6aab_graduation_permanently_disabled c791a6aab_graduation_permanently_disabled))
(assert
 (= c791a6aab_pair_deployed_before_graduation c791a6aab_pair_deployed_before_graduation))
(assert
 (= c791a6aab_token_near_graduation c791a6aab_token_near_graduation))
(define-fun report_preconditions () Bool (and c791a6aab_token_near_graduation c791a6aab_pair_deployed_before_graduation))
(define-fun report_safety () Bool (=> (and c791a6aab_token_near_graduation
         c791a6aab_pair_deployed_before_graduation)
    (and c791a6aab_graduation_completes
         (not c791a6aab_graduation_permanently_disabled))))
(define-fun report_effects () Bool (and c791a6aab_token_near_graduation
     c791a6aab_pair_deployed_before_graduation
     (not (and c791a6aab_graduation_completes
               (not c791a6aab_graduation_permanently_disabled)))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
