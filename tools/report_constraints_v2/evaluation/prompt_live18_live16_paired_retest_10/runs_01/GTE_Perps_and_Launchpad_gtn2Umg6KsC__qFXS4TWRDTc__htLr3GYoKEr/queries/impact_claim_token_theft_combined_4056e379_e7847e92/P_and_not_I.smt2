; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c39deaf1a_accounting_increased_before_transfer () Bool)
(declare-fun c39deaf1a_malicious_token_can_execute_during_transfer () Bool)
(declare-fun c39deaf1a_reentry_into_claim_rewards_during_transfer () Bool)
(declare-fun c39deaf1a_tokens_stolen_via_combined_weaknesses () Bool)
(assert
 (= c39deaf1a_accounting_increased_before_transfer c39deaf1a_accounting_increased_before_transfer))
(assert
 (= c39deaf1a_malicious_token_can_execute_during_transfer c39deaf1a_malicious_token_can_execute_during_transfer))
(assert
 (= c39deaf1a_reentry_into_claim_rewards_during_transfer c39deaf1a_reentry_into_claim_rewards_during_transfer))
(assert
 (= c39deaf1a_tokens_stolen_via_combined_weaknesses c39deaf1a_tokens_stolen_via_combined_weaknesses))
(define-fun report_preconditions () Bool c39deaf1a_malicious_token_can_execute_during_transfer)
(define-fun report_safety () Bool (=> c39deaf1a_tokens_stolen_via_combined_weaknesses
    (=> (and c39deaf1a_malicious_token_can_execute_during_transfer
             c39deaf1a_accounting_increased_before_transfer)
        (not c39deaf1a_reentry_into_claim_rewards_during_transfer))))
(define-fun report_effects () Bool (and c39deaf1a_tokens_stolen_via_combined_weaknesses
     c39deaf1a_malicious_token_can_execute_during_transfer
     c39deaf1a_accounting_increased_before_transfer
     (not (not c39deaf1a_reentry_into_claim_rewards_during_transfer))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
