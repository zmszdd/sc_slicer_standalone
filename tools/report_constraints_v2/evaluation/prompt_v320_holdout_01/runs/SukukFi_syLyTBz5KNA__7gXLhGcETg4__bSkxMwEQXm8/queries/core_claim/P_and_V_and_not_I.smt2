; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun assets_invested () Bool)
(declare-fun main_vault_balance_zero () Bool)
(declare-fun users_hold_shares () Bool)
(declare-fun invested_assets_tracked () Bool)
(declare-fun unregistration_succeeds () Bool)
(assert
 (= assets_invested assets_invested))
(assert
 (= main_vault_balance_zero main_vault_balance_zero))
(assert
 (= users_hold_shares users_hold_shares))
(assert
 (= invested_assets_tracked invested_assets_tracked))
(assert
 (= unregistration_succeeds unregistration_succeeds))
(define-fun report_preconditions () Bool (and assets_invested
     main_vault_balance_zero
     users_hold_shares
     invested_assets_tracked))
(define-fun report_safety () Bool (=> (and assets_invested users_hold_shares invested_assets_tracked)
    (not unregistration_succeeds)))
(define-fun report_effects () Bool (and assets_invested
     users_hold_shares
     invested_assets_tracked
     (not (not unregistration_succeeds))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
