; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4c019c6d_graduation_completed () Bool)
(declare-fun c4c019c6d_pair_precreated_by_attacker () Bool)
(declare-fun c4c019c6d_token_near_graduation () Bool)
(declare-fun c4c019c6d_token_transfer_restricted () Bool)
(declare-fun c4c019c6d_users_forced_to_pull_quote () Bool)
(assert
 (= c4c019c6d_graduation_completed c4c019c6d_graduation_completed))
(assert
 (= c4c019c6d_pair_precreated_by_attacker c4c019c6d_pair_precreated_by_attacker))
(assert
 (= c4c019c6d_token_near_graduation c4c019c6d_token_near_graduation))
(assert
 (= c4c019c6d_token_transfer_restricted c4c019c6d_token_transfer_restricted))
(assert
 (= c4c019c6d_users_forced_to_pull_quote c4c019c6d_users_forced_to_pull_quote))
(define-fun report_preconditions () Bool (and c4c019c6d_token_near_graduation
     c4c019c6d_pair_precreated_by_attacker
     c4c019c6d_token_transfer_restricted))
(define-fun report_safety () Bool (=> c4c019c6d_token_near_graduation
    (and c4c019c6d_graduation_completed
         (not c4c019c6d_users_forced_to_pull_quote))))
(define-fun report_effects () Bool (and c4c019c6d_token_near_graduation
     (not (and c4c019c6d_graduation_completed
               (not c4c019c6d_users_forced_to_pull_quote)))))
