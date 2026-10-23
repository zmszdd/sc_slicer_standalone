; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2d6a4574_blp_reserve_exists () Bool)
(declare-fun c2d6a4574_pm_active () Bool)
(declare-fun c2d6a4574_supplied_balance_reverts () Bool)
(declare-fun c2d6a4574_token_registered_in_vault_supplied () Bool)
(assert
 (= c2d6a4574_blp_reserve_exists c2d6a4574_blp_reserve_exists))
(assert
 (= c2d6a4574_pm_active c2d6a4574_pm_active))
(assert
 (= c2d6a4574_supplied_balance_reverts c2d6a4574_supplied_balance_reverts))
(assert
 (= c2d6a4574_token_registered_in_vault_supplied c2d6a4574_token_registered_in_vault_supplied))
(define-fun report_preconditions () Bool (and c2d6a4574_pm_active (not c2d6a4574_blp_reserve_exists)))
(define-fun report_safety () Bool (=> (and c2d6a4574_pm_active
         (not c2d6a4574_blp_reserve_exists)
         c2d6a4574_token_registered_in_vault_supplied)
    (not c2d6a4574_supplied_balance_reverts)))
(define-fun report_effects () Bool (and c2d6a4574_pm_active
     (not c2d6a4574_blp_reserve_exists)
     c2d6a4574_token_registered_in_vault_supplied
     (not (not c2d6a4574_supplied_balance_reverts))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
