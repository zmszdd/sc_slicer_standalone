; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c847d2f65_alice_is_blacklisted () Bool)
(declare-fun c847d2f65_blacklist_blocks_transfer () Bool)
(declare-fun c847d2f65_cooldown_completed () Bool)
(declare-fun c847d2f65_tokens_locked_in_adapter () Bool)
(declare-fun c847d2f65_unstake_callable_by_blacklisted () Bool)
(assert
 (= c847d2f65_alice_is_blacklisted c847d2f65_alice_is_blacklisted))
(assert
 (= c847d2f65_blacklist_blocks_transfer c847d2f65_blacklist_blocks_transfer))
(assert
 (= c847d2f65_cooldown_completed c847d2f65_cooldown_completed))
(assert
 (= c847d2f65_tokens_locked_in_adapter c847d2f65_tokens_locked_in_adapter))
(assert
 (= c847d2f65_unstake_callable_by_blacklisted c847d2f65_unstake_callable_by_blacklisted))
(define-fun report_preconditions () Bool (and c847d2f65_alice_is_blacklisted
     c847d2f65_cooldown_completed
     c847d2f65_blacklist_blocks_transfer
     c847d2f65_unstake_callable_by_blacklisted))
(define-fun report_safety () Bool (=> (and c847d2f65_alice_is_blacklisted
         c847d2f65_cooldown_completed
         c847d2f65_blacklist_blocks_transfer
         c847d2f65_unstake_callable_by_blacklisted)
    (not c847d2f65_tokens_locked_in_adapter)))
(define-fun report_effects () Bool (and c847d2f65_alice_is_blacklisted
     c847d2f65_cooldown_completed
     c847d2f65_blacklist_blocks_transfer
     c847d2f65_unstake_callable_by_blacklisted
     (not (not c847d2f65_tokens_locked_in_adapter))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
