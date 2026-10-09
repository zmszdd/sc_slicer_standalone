; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun vault_token_balance () Int)
(declare-fun invested_assets_tracked () Bool)
(declare-fun outstanding_user_shares_exist () Bool)
(declare-fun asset_investment_via_investassets () Bool)
(declare-fun vault_unregistered () Bool)
(assert
 (= vault_token_balance vault_token_balance))
(assert
 (= invested_assets_tracked invested_assets_tracked))
(assert
 (= outstanding_user_shares_exist outstanding_user_shares_exist))
(assert
 (= asset_investment_via_investassets asset_investment_via_investassets))
(assert
 (= vault_unregistered vault_unregistered))
(define-fun report_preconditions () Bool (and asset_investment_via_investassets
     (= 0 vault_token_balance)
     outstanding_user_shares_exist))
(define-fun report_safety () Bool (=> (and asset_investment_via_investassets
         (= 0 vault_token_balance)
         outstanding_user_shares_exist
         invested_assets_tracked)
    (not vault_unregistered)))
(define-fun report_effects () Bool (and asset_investment_via_investassets
     (= 0 vault_token_balance)
     outstanding_user_shares_exist
     invested_assets_tracked
     (not (not vault_unregistered))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
