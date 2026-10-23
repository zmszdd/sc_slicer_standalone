; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6a8ced2f_graduation_completed () Bool)
(declare-fun c6a8ced2f_graduation_permanently_disabled () Bool)
(declare-fun c6a8ced2f_pair_deployed_before_graduation () Bool)
(declare-fun c6a8ced2f_pair_token_reserve_wei () Int)
(declare-fun c6a8ced2f_token_near_graduation () Bool)
(assert
 (= c6a8ced2f_graduation_completed c6a8ced2f_graduation_completed))
(assert
 (= c6a8ced2f_graduation_permanently_disabled c6a8ced2f_graduation_permanently_disabled))
(assert
 (= c6a8ced2f_pair_deployed_before_graduation c6a8ced2f_pair_deployed_before_graduation))
(assert
 (= c6a8ced2f_pair_token_reserve_wei c6a8ced2f_pair_token_reserve_wei))
(assert
 (= c6a8ced2f_token_near_graduation c6a8ced2f_token_near_graduation))
(define-fun report_preconditions () Bool (and c6a8ced2f_token_near_graduation
     c6a8ced2f_pair_deployed_before_graduation
     (= 1 c6a8ced2f_pair_token_reserve_wei)))
(define-fun report_safety () Bool (=> (and c6a8ced2f_token_near_graduation
         c6a8ced2f_pair_deployed_before_graduation
         (= 1 c6a8ced2f_pair_token_reserve_wei))
    (and c6a8ced2f_graduation_completed
         (not c6a8ced2f_graduation_permanently_disabled))))
(define-fun report_effects () Bool (and c6a8ced2f_token_near_graduation
     c6a8ced2f_pair_deployed_before_graduation
     (= 1 c6a8ced2f_pair_token_reserve_wei)
     (not (and c6a8ced2f_graduation_completed
               (not c6a8ced2f_graduation_permanently_disabled)))))
(assert report_preconditions)
(check-sat)
(get-model)
