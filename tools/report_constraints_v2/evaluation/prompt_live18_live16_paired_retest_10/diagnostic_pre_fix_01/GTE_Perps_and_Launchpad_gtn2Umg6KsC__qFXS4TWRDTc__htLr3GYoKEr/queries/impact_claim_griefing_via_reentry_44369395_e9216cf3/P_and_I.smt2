; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c09dd232b_griefing_occurs () Bool)
(declare-fun c09dd232b_reentry_into_claim_rewards_during_transfer_from () Bool)
(declare-fun c09dd232b_reward_token_malicious () Bool)
(assert
 (= c09dd232b_griefing_occurs c09dd232b_griefing_occurs))
(assert
 (= c09dd232b_reentry_into_claim_rewards_during_transfer_from c09dd232b_reentry_into_claim_rewards_during_transfer_from))
(assert
 (= c09dd232b_reward_token_malicious c09dd232b_reward_token_malicious))
(define-fun report_preconditions () Bool c09dd232b_reward_token_malicious)
(define-fun report_safety () Bool (=> c09dd232b_griefing_occurs
    (=> c09dd232b_reward_token_malicious
        (not c09dd232b_reentry_into_claim_rewards_during_transfer_from))))
(define-fun report_effects () Bool (and c09dd232b_griefing_occurs
     c09dd232b_reward_token_malicious
     (not (not c09dd232b_reentry_into_claim_rewards_during_transfer_from))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
