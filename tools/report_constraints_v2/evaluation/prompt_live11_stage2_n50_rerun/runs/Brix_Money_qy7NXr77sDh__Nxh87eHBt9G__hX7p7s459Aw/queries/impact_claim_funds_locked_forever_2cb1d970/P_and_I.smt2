; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cf9d7a389_alice_is_blacklisted () Bool)
(declare-fun cf9d7a389_cooldown_completed () Bool)
(declare-fun cf9d7a389_funds_locked_in_adapter () Bool)
(declare-fun cf9d7a389_transfer_blocked_for_blacklisted () Bool)
(declare-fun cf9d7a389_unstake_callable () Bool)
(assert
 (= cf9d7a389_alice_is_blacklisted cf9d7a389_alice_is_blacklisted))
(assert
 (= cf9d7a389_cooldown_completed cf9d7a389_cooldown_completed))
(assert
 (= cf9d7a389_funds_locked_in_adapter cf9d7a389_funds_locked_in_adapter))
(assert
 (= cf9d7a389_transfer_blocked_for_blacklisted cf9d7a389_transfer_blocked_for_blacklisted))
(assert
 (= cf9d7a389_unstake_callable cf9d7a389_unstake_callable))
(define-fun report_preconditions () Bool (and cf9d7a389_alice_is_blacklisted
     cf9d7a389_cooldown_completed
     cf9d7a389_unstake_callable
     cf9d7a389_transfer_blocked_for_blacklisted))
(define-fun report_safety () Bool (=> (and cf9d7a389_alice_is_blacklisted
         cf9d7a389_cooldown_completed
         cf9d7a389_unstake_callable
         cf9d7a389_transfer_blocked_for_blacklisted)
    (not cf9d7a389_funds_locked_in_adapter)))
(define-fun report_effects () Bool (and cf9d7a389_alice_is_blacklisted
     cf9d7a389_cooldown_completed
     cf9d7a389_unstake_callable
     cf9d7a389_transfer_blocked_for_blacklisted
     (not (not cf9d7a389_funds_locked_in_adapter))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
