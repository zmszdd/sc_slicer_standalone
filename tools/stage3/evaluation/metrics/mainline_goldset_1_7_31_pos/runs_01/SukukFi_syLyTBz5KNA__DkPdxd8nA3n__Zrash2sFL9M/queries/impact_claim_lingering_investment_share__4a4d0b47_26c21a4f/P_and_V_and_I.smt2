; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9e7182cf_allowance_after_unregister () Int)
(declare-fun c9e7182cf_investment_share_token_configured () Bool)
(declare-fun c9e7182cf_vault_registered_with_max_allowance () Bool)
(declare-fun c9e7182cf_vault_unregistered () Bool)
(declare-fun c9e7182cf_zero_allowance () Int)
(assert
 (= c9e7182cf_allowance_after_unregister c9e7182cf_allowance_after_unregister))
(assert
 (= c9e7182cf_investment_share_token_configured c9e7182cf_investment_share_token_configured))
(assert
 (= c9e7182cf_vault_registered_with_max_allowance c9e7182cf_vault_registered_with_max_allowance))
(assert
 (= c9e7182cf_vault_unregistered c9e7182cf_vault_unregistered))
(assert
 (= c9e7182cf_zero_allowance c9e7182cf_zero_allowance))
(define-fun report_preconditions () Bool (and c9e7182cf_investment_share_token_configured
     c9e7182cf_vault_registered_with_max_allowance
     c9e7182cf_vault_unregistered))
(define-fun report_safety () Bool (= c9e7182cf_allowance_after_unregister c9e7182cf_zero_allowance))
(define-fun report_effects () Bool (and c9e7182cf_vault_unregistered
     (not (= c9e7182cf_allowance_after_unregister c9e7182cf_zero_allowance))
     (> c9e7182cf_allowance_after_unregister c9e7182cf_zero_allowance)
     c9e7182cf_vault_unregistered))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
