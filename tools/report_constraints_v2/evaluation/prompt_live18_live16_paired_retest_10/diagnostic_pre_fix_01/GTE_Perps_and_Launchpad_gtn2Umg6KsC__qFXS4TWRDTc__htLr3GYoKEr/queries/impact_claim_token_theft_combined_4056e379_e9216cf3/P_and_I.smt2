; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c489bc6e6_reentry_into_claim_rewards_during_transfer_from () Bool)
(declare-fun c489bc6e6_reward_token_malicious () Bool)
(declare-fun c489bc6e6_tokens_stolen_via_combined_weaknesses () Bool)
(assert
 (= c489bc6e6_reentry_into_claim_rewards_during_transfer_from c489bc6e6_reentry_into_claim_rewards_during_transfer_from))
(assert
 (= c489bc6e6_reward_token_malicious c489bc6e6_reward_token_malicious))
(assert
 (= c489bc6e6_tokens_stolen_via_combined_weaknesses c489bc6e6_tokens_stolen_via_combined_weaknesses))
(define-fun report_preconditions () Bool c489bc6e6_reward_token_malicious)
(define-fun report_safety () Bool (=> c489bc6e6_tokens_stolen_via_combined_weaknesses
    (=> c489bc6e6_reentry_into_claim_rewards_during_transfer_from
        (not c489bc6e6_reward_token_malicious))))
(define-fun report_effects () Bool (and c489bc6e6_tokens_stolen_via_combined_weaknesses
     c489bc6e6_reentry_into_claim_rewards_during_transfer_from
     (not (not c489bc6e6_reward_token_malicious))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
