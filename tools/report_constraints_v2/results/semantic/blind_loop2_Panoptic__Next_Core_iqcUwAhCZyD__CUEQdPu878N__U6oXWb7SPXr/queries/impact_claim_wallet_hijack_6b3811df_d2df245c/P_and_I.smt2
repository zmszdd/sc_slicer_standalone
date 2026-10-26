; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8f4569db_init_callable_by_any () Bool)
(declare-fun c8f4569db_init_recalled_by_attacker () Bool)
(declare-fun c8f4569db_init_reinit_protected () Bool)
(declare-fun c8f4569db_init_restricted_to_factory () Bool)
(declare-fun c8f4569db_wallet_deployed_by_factory () Bool)
(declare-fun c8f4569db_wallet_hijacked () Bool)
(assert
 (= c8f4569db_init_callable_by_any c8f4569db_init_callable_by_any))
(assert
 (= c8f4569db_init_recalled_by_attacker c8f4569db_init_recalled_by_attacker))
(assert
 (= c8f4569db_init_reinit_protected c8f4569db_init_reinit_protected))
(assert
 (= c8f4569db_init_restricted_to_factory c8f4569db_init_restricted_to_factory))
(assert
 (= c8f4569db_wallet_deployed_by_factory c8f4569db_wallet_deployed_by_factory))
(assert
 (= c8f4569db_wallet_hijacked c8f4569db_wallet_hijacked))
(define-fun report_preconditions () Bool (and c8f4569db_wallet_deployed_by_factory
     c8f4569db_init_callable_by_any
     (not c8f4569db_init_restricted_to_factory)
     (not c8f4569db_init_reinit_protected)))
(define-fun report_safety () Bool (=> c8f4569db_init_recalled_by_attacker c8f4569db_init_reinit_protected))
(define-fun report_effects () Bool (and c8f4569db_init_recalled_by_attacker c8f4569db_wallet_hijacked))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
