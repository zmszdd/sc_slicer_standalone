; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb7277238_alice_is_blacklisted () Bool)
(declare-fun cb7277238_before_transfer_blocks_blacklisted () Bool)
(declare-fun cb7277238_cooldown_completed () Bool)
(declare-fun cb7277238_tokens_locked_in_adapter () Bool)
(declare-fun cb7277238_unstake_callable_by_blacklisted () Bool)
(assert
 (= cb7277238_alice_is_blacklisted cb7277238_alice_is_blacklisted))
(assert
 (= cb7277238_before_transfer_blocks_blacklisted cb7277238_before_transfer_blocks_blacklisted))
(assert
 (= cb7277238_cooldown_completed cb7277238_cooldown_completed))
(assert
 (= cb7277238_tokens_locked_in_adapter cb7277238_tokens_locked_in_adapter))
(assert
 (= cb7277238_unstake_callable_by_blacklisted cb7277238_unstake_callable_by_blacklisted))
(define-fun report_preconditions () Bool (and cb7277238_alice_is_blacklisted
     cb7277238_cooldown_completed
     cb7277238_unstake_callable_by_blacklisted
     cb7277238_before_transfer_blocks_blacklisted))
(define-fun report_safety () Bool (=> (and cb7277238_alice_is_blacklisted
         cb7277238_cooldown_completed
         cb7277238_unstake_callable_by_blacklisted
         cb7277238_before_transfer_blocks_blacklisted)
    (not cb7277238_tokens_locked_in_adapter)))
(define-fun report_effects () Bool (and cb7277238_alice_is_blacklisted
     cb7277238_cooldown_completed
     cb7277238_unstake_callable_by_blacklisted
     cb7277238_before_transfer_blocks_blacklisted
     (not (not cb7277238_tokens_locked_in_adapter))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
