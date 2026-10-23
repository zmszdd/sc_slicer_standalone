; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2f936598_graduation_completed () Bool)
(declare-fun c2f936598_pair_deployed_before_graduation () Bool)
(declare-fun c2f936598_token_near_graduation () Bool)
(declare-fun c2f936598_tokens_movable_to_pair () Bool)
(assert
 (= c2f936598_graduation_completed c2f936598_graduation_completed))
(assert
 (= c2f936598_pair_deployed_before_graduation c2f936598_pair_deployed_before_graduation))
(assert
 (= c2f936598_token_near_graduation c2f936598_token_near_graduation))
(assert
 (= c2f936598_tokens_movable_to_pair c2f936598_tokens_movable_to_pair))
(define-fun report_preconditions () Bool (and c2f936598_token_near_graduation c2f936598_pair_deployed_before_graduation))
(define-fun report_safety () Bool (=> (and c2f936598_token_near_graduation
         c2f936598_pair_deployed_before_graduation)
    (and c2f936598_graduation_completed c2f936598_tokens_movable_to_pair)))
(define-fun report_effects () Bool (and c2f936598_token_near_graduation
     c2f936598_pair_deployed_before_graduation
     (not (and c2f936598_graduation_completed c2f936598_tokens_movable_to_pair))))
