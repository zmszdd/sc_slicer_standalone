; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c04be7e7b_builder_admin_set_before () Bool)
(declare-fun c04be7e7b_reinit_succeeded () Bool)
(declare-fun c04be7e7b_tokens_stolen () Bool)
(declare-fun c04be7e7b_wallet_deployed_by_factory_done () Bool)
(declare-fun c04be7e7b_wallet_token_balance_before () Int)
(assert
 (= c04be7e7b_builder_admin_set_before c04be7e7b_builder_admin_set_before))
(assert
 (= c04be7e7b_reinit_succeeded c04be7e7b_reinit_succeeded))
(assert
 (= c04be7e7b_tokens_stolen c04be7e7b_tokens_stolen))
(assert
 (= c04be7e7b_wallet_deployed_by_factory_done c04be7e7b_wallet_deployed_by_factory_done))
(assert
 (= c04be7e7b_wallet_token_balance_before c04be7e7b_wallet_token_balance_before))
(define-fun report_preconditions () Bool (and c04be7e7b_wallet_deployed_by_factory_done
     c04be7e7b_builder_admin_set_before
     (< 0 c04be7e7b_wallet_token_balance_before)))
(define-fun report_safety () Bool (=> c04be7e7b_tokens_stolen
    (=> c04be7e7b_reinit_succeeded (not c04be7e7b_builder_admin_set_before))))
(define-fun report_effects () Bool (and c04be7e7b_tokens_stolen
     c04be7e7b_reinit_succeeded
     (not (not c04be7e7b_builder_admin_set_before))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
