; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c39deaf1a_add_rewards_token_reentrant () Bool)
(declare-fun c39deaf1a_claim_rewards_entered_in_window () Bool)
(declare-fun c39deaf1a_reentrancy_guard_absent () Bool)
(declare-fun c39deaf1a_tokens_stolen_combined () Bool)
(assert
 (= c39deaf1a_add_rewards_token_reentrant c39deaf1a_add_rewards_token_reentrant))
(assert
 (= c39deaf1a_claim_rewards_entered_in_window c39deaf1a_claim_rewards_entered_in_window))
(assert
 (= c39deaf1a_reentrancy_guard_absent c39deaf1a_reentrancy_guard_absent))
(assert
 (= c39deaf1a_tokens_stolen_combined c39deaf1a_tokens_stolen_combined))
(define-fun report_preconditions () Bool (and c39deaf1a_add_rewards_token_reentrant c39deaf1a_reentrancy_guard_absent))
(define-fun report_safety () Bool (=> c39deaf1a_tokens_stolen_combined
    (=> (and c39deaf1a_add_rewards_token_reentrant
             c39deaf1a_reentrancy_guard_absent)
        (not c39deaf1a_claim_rewards_entered_in_window))))
(define-fun report_effects () Bool (and c39deaf1a_tokens_stolen_combined
     c39deaf1a_add_rewards_token_reentrant
     c39deaf1a_reentrancy_guard_absent
     (not (not c39deaf1a_claim_rewards_entered_in_window))))
(assert report_preconditions)
(check-sat)
(get-model)
