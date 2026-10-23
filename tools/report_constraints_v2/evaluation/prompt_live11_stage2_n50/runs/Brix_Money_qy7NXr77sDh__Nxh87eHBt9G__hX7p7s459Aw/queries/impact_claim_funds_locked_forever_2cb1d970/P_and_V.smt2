; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cf9d7a389_alice_is_blacklisted () Bool)
(declare-fun cf9d7a389_blacklist_blocks_transfer () Bool)
(declare-fun cf9d7a389_cooldown_completed () Bool)
(declare-fun cf9d7a389_funds_locked_in_adapter_forever () Bool)
(declare-fun cf9d7a389_unstake_callable_by_blacklisted () Bool)
(assert
 (= cf9d7a389_alice_is_blacklisted cf9d7a389_alice_is_blacklisted))
(assert
 (= cf9d7a389_blacklist_blocks_transfer cf9d7a389_blacklist_blocks_transfer))
(assert
 (= cf9d7a389_cooldown_completed cf9d7a389_cooldown_completed))
(assert
 (= cf9d7a389_funds_locked_in_adapter_forever cf9d7a389_funds_locked_in_adapter_forever))
(assert
 (= cf9d7a389_unstake_callable_by_blacklisted cf9d7a389_unstake_callable_by_blacklisted))
(define-fun report_preconditions () Bool (and cf9d7a389_alice_is_blacklisted
     cf9d7a389_cooldown_completed
     cf9d7a389_blacklist_blocks_transfer
     cf9d7a389_unstake_callable_by_blacklisted))
(define-fun report_safety () Bool (=> (and cf9d7a389_alice_is_blacklisted
         cf9d7a389_cooldown_completed
         cf9d7a389_blacklist_blocks_transfer
         cf9d7a389_unstake_callable_by_blacklisted)
    (not cf9d7a389_funds_locked_in_adapter_forever)))
(define-fun report_effects () Bool (and cf9d7a389_alice_is_blacklisted
     cf9d7a389_cooldown_completed
     cf9d7a389_blacklist_blocks_transfer
     cf9d7a389_unstake_callable_by_blacklisted
     (not (not cf9d7a389_funds_locked_in_adapter_forever))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
