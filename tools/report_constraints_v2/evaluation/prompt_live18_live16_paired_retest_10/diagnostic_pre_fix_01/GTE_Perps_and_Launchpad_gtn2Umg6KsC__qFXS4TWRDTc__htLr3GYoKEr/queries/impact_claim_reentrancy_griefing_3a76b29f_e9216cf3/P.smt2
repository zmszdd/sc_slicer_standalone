; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca432d257_reentrancy_window_created () Bool)
(declare-fun ca432d257_reentry_during_transferfrom () Bool)
(declare-fun ca432d257_reward_token_malicious () Bool)
(assert
 (= ca432d257_reentrancy_window_created ca432d257_reentrancy_window_created))
(assert
 (= ca432d257_reentry_during_transferfrom ca432d257_reentry_during_transferfrom))
(assert
 (= ca432d257_reward_token_malicious ca432d257_reward_token_malicious))
(define-fun report_preconditions () Bool ca432d257_reward_token_malicious)
(define-fun report_safety () Bool (=> ca432d257_reentrancy_window_created
    (=> ca432d257_reward_token_malicious
        (not ca432d257_reentry_during_transferfrom))))
(define-fun report_effects () Bool (and ca432d257_reentrancy_window_created
     ca432d257_reward_token_malicious
     (not (not ca432d257_reentry_during_transferfrom))))
(assert report_preconditions)
(check-sat)
(get-model)
