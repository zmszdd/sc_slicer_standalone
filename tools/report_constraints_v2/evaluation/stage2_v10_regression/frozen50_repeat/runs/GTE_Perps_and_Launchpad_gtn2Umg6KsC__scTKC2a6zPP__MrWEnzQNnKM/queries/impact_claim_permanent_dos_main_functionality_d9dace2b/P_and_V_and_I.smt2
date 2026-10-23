; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cea148b22_graduation_completed () Bool)
(declare-fun cea148b22_graduation_permanently_disabled () Bool)
(declare-fun cea148b22_pair_created_before_graduation () Bool)
(declare-fun cea148b22_token_near_graduation () Bool)
(declare-fun cea148b22_token_transfer_restricted () Bool)
(assert
 (= cea148b22_graduation_completed cea148b22_graduation_completed))
(assert
 (= cea148b22_graduation_permanently_disabled cea148b22_graduation_permanently_disabled))
(assert
 (= cea148b22_pair_created_before_graduation cea148b22_pair_created_before_graduation))
(assert
 (= cea148b22_token_near_graduation cea148b22_token_near_graduation))
(assert
 (= cea148b22_token_transfer_restricted cea148b22_token_transfer_restricted))
(define-fun report_preconditions () Bool (and cea148b22_token_near_graduation
     cea148b22_pair_created_before_graduation
     cea148b22_token_transfer_restricted))
(define-fun report_safety () Bool (=> (and cea148b22_token_near_graduation
         cea148b22_pair_created_before_graduation
         cea148b22_token_transfer_restricted)
    (and cea148b22_graduation_completed
         (not cea148b22_graduation_permanently_disabled))))
(define-fun report_effects () Bool (and cea148b22_token_near_graduation
     cea148b22_pair_created_before_graduation
     cea148b22_token_transfer_restricted
     (not (and cea148b22_graduation_completed
               (not cea148b22_graduation_permanently_disabled)))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
