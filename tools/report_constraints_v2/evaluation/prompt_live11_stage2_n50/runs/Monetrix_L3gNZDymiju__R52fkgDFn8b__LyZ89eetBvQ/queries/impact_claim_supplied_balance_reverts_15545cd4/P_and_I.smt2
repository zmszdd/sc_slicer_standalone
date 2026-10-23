; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9b19343b_blp_reserve_exists () Bool)
(declare-fun c9b19343b_pm_active () Bool)
(declare-fun c9b19343b_supplied_balance_reverts () Bool)
(declare-fun c9b19343b_token_registered_in_vault_supplied () Bool)
(assert
 (= c9b19343b_blp_reserve_exists c9b19343b_blp_reserve_exists))
(assert
 (= c9b19343b_pm_active c9b19343b_pm_active))
(assert
 (= c9b19343b_supplied_balance_reverts c9b19343b_supplied_balance_reverts))
(assert
 (= c9b19343b_token_registered_in_vault_supplied c9b19343b_token_registered_in_vault_supplied))
(define-fun report_preconditions () Bool (and c9b19343b_pm_active (not c9b19343b_blp_reserve_exists)))
(define-fun report_safety () Bool (=> (and c9b19343b_pm_active
         (not c9b19343b_blp_reserve_exists)
         c9b19343b_token_registered_in_vault_supplied)
    (not c9b19343b_supplied_balance_reverts)))
(define-fun report_effects () Bool (and c9b19343b_pm_active
     (not c9b19343b_blp_reserve_exists)
     c9b19343b_token_registered_in_vault_supplied
     (not (not c9b19343b_supplied_balance_reverts))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
