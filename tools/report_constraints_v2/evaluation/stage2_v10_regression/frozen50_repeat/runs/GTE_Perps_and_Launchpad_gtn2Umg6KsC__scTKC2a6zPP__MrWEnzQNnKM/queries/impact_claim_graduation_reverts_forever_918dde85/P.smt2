; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0a621d8e_graduation_completed () Bool)
(declare-fun c0a621d8e_graduation_reverted () Bool)
(declare-fun c0a621d8e_pair_created_before_graduation () Bool)
(declare-fun c0a621d8e_token_near_graduation () Bool)
(declare-fun c0a621d8e_token_transfer_restricted_until_graduation () Bool)
(assert
 (= c0a621d8e_graduation_completed c0a621d8e_graduation_completed))
(assert
 (= c0a621d8e_graduation_reverted c0a621d8e_graduation_reverted))
(assert
 (= c0a621d8e_pair_created_before_graduation c0a621d8e_pair_created_before_graduation))
(assert
 (= c0a621d8e_token_near_graduation c0a621d8e_token_near_graduation))
(assert
 (= c0a621d8e_token_transfer_restricted_until_graduation c0a621d8e_token_transfer_restricted_until_graduation))
(define-fun report_preconditions () Bool (and c0a621d8e_token_near_graduation
     c0a621d8e_pair_created_before_graduation
     c0a621d8e_token_transfer_restricted_until_graduation))
(define-fun report_safety () Bool (=> (and c0a621d8e_token_near_graduation
         c0a621d8e_pair_created_before_graduation
         c0a621d8e_token_transfer_restricted_until_graduation)
    (and c0a621d8e_graduation_completed (not c0a621d8e_graduation_reverted))))
(define-fun report_effects () Bool (and c0a621d8e_token_near_graduation
     c0a621d8e_pair_created_before_graduation
     c0a621d8e_token_transfer_restricted_until_graduation
     (not (and c0a621d8e_graduation_completed
               (not c0a621d8e_graduation_reverted)))))
(assert report_preconditions)
(check-sat)
(get-model)
