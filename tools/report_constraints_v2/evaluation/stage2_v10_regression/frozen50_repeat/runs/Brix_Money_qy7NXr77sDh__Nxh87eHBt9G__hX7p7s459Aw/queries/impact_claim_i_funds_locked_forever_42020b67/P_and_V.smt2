; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c362e2c69_adapter_locked_tokens () Int)
(declare-fun c362e2c69_alice_blacklisted () Bool)
(declare-fun c362e2c69_blacklist_blocks_transfer () Bool)
(declare-fun c362e2c69_cooldown_tokens () Int)
(declare-fun c362e2c69_funds_locked_forever () Bool)
(declare-fun c362e2c69_unstake_callable_by_blacklisted () Bool)
(assert
 (= c362e2c69_adapter_locked_tokens c362e2c69_adapter_locked_tokens))
(assert
 (= c362e2c69_alice_blacklisted c362e2c69_alice_blacklisted))
(assert
 (= c362e2c69_blacklist_blocks_transfer c362e2c69_blacklist_blocks_transfer))
(assert
 (= c362e2c69_cooldown_tokens c362e2c69_cooldown_tokens))
(assert
 (= c362e2c69_funds_locked_forever c362e2c69_funds_locked_forever))
(assert
 (= c362e2c69_unstake_callable_by_blacklisted c362e2c69_unstake_callable_by_blacklisted))
(define-fun report_preconditions () Bool (and c362e2c69_alice_blacklisted
     (= 100 c362e2c69_cooldown_tokens)
     c362e2c69_blacklist_blocks_transfer
     c362e2c69_unstake_callable_by_blacklisted))
(define-fun report_safety () Bool (=> (and c362e2c69_alice_blacklisted
         (= 100 c362e2c69_cooldown_tokens)
         c362e2c69_blacklist_blocks_transfer
         c362e2c69_unstake_callable_by_blacklisted)
    (and (= 0 c362e2c69_adapter_locked_tokens)
         (not c362e2c69_funds_locked_forever))))
(define-fun report_effects () Bool (and c362e2c69_alice_blacklisted
     (= 100 c362e2c69_cooldown_tokens)
     c362e2c69_blacklist_blocks_transfer
     c362e2c69_unstake_callable_by_blacklisted
     (not (and (= 0 c362e2c69_adapter_locked_tokens)
               (not c362e2c69_funds_locked_forever)))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
