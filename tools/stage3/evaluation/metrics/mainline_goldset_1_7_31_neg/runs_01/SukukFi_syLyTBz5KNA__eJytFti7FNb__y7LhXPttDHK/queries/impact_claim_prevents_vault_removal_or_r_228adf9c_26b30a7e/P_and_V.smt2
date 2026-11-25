; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c03a5ada5_asset_balance_nonzero () Bool)
(declare-fun c03a5ada5_removal_or_replacement_prevented () Bool)
(declare-fun c03a5ada5_single_vault_per_asset () Bool)
(declare-fun c03a5ada5_vault_issue_arises () Bool)
(declare-fun c03a5ada5_vault_registered () Bool)
(declare-fun c03a5ada5_vault_retired () Bool)
(assert
 (= c03a5ada5_asset_balance_nonzero c03a5ada5_asset_balance_nonzero))
(assert
 (= c03a5ada5_removal_or_replacement_prevented c03a5ada5_removal_or_replacement_prevented))
(assert
 (= c03a5ada5_single_vault_per_asset c03a5ada5_single_vault_per_asset))
(assert
 (= c03a5ada5_vault_issue_arises c03a5ada5_vault_issue_arises))
(assert
 (= c03a5ada5_vault_registered c03a5ada5_vault_registered))
(assert
 (= c03a5ada5_vault_retired c03a5ada5_vault_retired))
(define-fun report_preconditions () Bool (and c03a5ada5_vault_registered
     c03a5ada5_single_vault_per_asset
     c03a5ada5_vault_issue_arises))
(define-fun report_safety () Bool (=> (and c03a5ada5_vault_registered c03a5ada5_asset_balance_nonzero)
    c03a5ada5_vault_retired))
(define-fun report_effects () Bool (and c03a5ada5_vault_registered
     c03a5ada5_asset_balance_nonzero
     (not c03a5ada5_vault_retired)
     c03a5ada5_removal_or_replacement_prevented))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
