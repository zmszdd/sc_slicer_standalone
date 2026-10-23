; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ccc1ebc8c_monetary_extraction_occurred () Bool)
(declare-fun ccc1ebc8c_reentry_into_claim_rewards_during_transfer_from () Bool)
(declare-fun ccc1ebc8c_reward_token_malicious () Bool)
(assert
 (= ccc1ebc8c_monetary_extraction_occurred ccc1ebc8c_monetary_extraction_occurred))
(assert
 (= ccc1ebc8c_reentry_into_claim_rewards_during_transfer_from ccc1ebc8c_reentry_into_claim_rewards_during_transfer_from))
(assert
 (= ccc1ebc8c_reward_token_malicious ccc1ebc8c_reward_token_malicious))
(define-fun report_preconditions () Bool ccc1ebc8c_reward_token_malicious)
(define-fun report_safety () Bool (=> ccc1ebc8c_monetary_extraction_occurred
    (=> ccc1ebc8c_reentry_into_claim_rewards_during_transfer_from
        (not ccc1ebc8c_reward_token_malicious))))
(define-fun report_effects () Bool (and ccc1ebc8c_monetary_extraction_occurred
     ccc1ebc8c_reentry_into_claim_rewards_during_transfer_from
     (not (not ccc1ebc8c_reward_token_malicious))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
