; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c095f818d_factory_vault_is_lpvault1 () Bool)
(declare-fun c095f818d_pair_uses_lpvault1 () Bool)
(declare-fun c095f818d_reward_fees_distributed () Bool)
(assert
 (= c095f818d_factory_vault_is_lpvault1 c095f818d_factory_vault_is_lpvault1))
(assert
 (= c095f818d_pair_uses_lpvault1 c095f818d_pair_uses_lpvault1))
(assert
 (= c095f818d_reward_fees_distributed c095f818d_reward_fees_distributed))
(define-fun report_preconditions () Bool (and c095f818d_factory_vault_is_lpvault1 c095f818d_pair_uses_lpvault1))
(define-fun report_safety () Bool (=> (and c095f818d_factory_vault_is_lpvault1 c095f818d_pair_uses_lpvault1)
    c095f818d_reward_fees_distributed))
(define-fun report_effects () Bool (and c095f818d_factory_vault_is_lpvault1
     c095f818d_pair_uses_lpvault1
     (not c095f818d_reward_fees_distributed)))
