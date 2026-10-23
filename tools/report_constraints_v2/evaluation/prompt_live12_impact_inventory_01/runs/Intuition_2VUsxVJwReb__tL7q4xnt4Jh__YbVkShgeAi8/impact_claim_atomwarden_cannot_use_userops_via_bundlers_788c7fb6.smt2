; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce7bf4453_multivault_staked_in_entrypoint () Bool)
(declare-fun ce7bf4453_userop_completed_via_bundler () Bool)
(declare-fun ce7bf4453_validate_userop_reads_unstaked_storage () Bool)
(declare-fun ce7bf4453_wallet_is_claimed () Bool)
(assert
 (= ce7bf4453_multivault_staked_in_entrypoint ce7bf4453_multivault_staked_in_entrypoint))
(assert
 (= ce7bf4453_userop_completed_via_bundler ce7bf4453_userop_completed_via_bundler))
(assert
 (= ce7bf4453_validate_userop_reads_unstaked_storage ce7bf4453_validate_userop_reads_unstaked_storage))
(assert
 (= ce7bf4453_wallet_is_claimed ce7bf4453_wallet_is_claimed))
(define-fun report_preconditions () Bool (and (not ce7bf4453_wallet_is_claimed)
     (not ce7bf4453_multivault_staked_in_entrypoint)))
(define-fun report_safety () Bool (=> (and (not ce7bf4453_wallet_is_claimed)
         (not ce7bf4453_multivault_staked_in_entrypoint))
    (and (not ce7bf4453_validate_userop_reads_unstaked_storage)
         ce7bf4453_userop_completed_via_bundler)))
(define-fun report_effects () Bool (and (not ce7bf4453_wallet_is_claimed)
     (not ce7bf4453_multivault_staked_in_entrypoint)
     (not (and (not ce7bf4453_validate_userop_reads_unstaked_storage)
               ce7bf4453_userop_completed_via_bundler))))
