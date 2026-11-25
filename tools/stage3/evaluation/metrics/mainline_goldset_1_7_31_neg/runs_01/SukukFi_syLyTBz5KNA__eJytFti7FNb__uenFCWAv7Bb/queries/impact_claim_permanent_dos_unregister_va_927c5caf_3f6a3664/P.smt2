; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbf01c716_unregister_vault_blocked () Bool)
(declare-fun cbf01c716_vault_erc20_balance () Int)
(assert
 (= cbf01c716_unregister_vault_blocked cbf01c716_unregister_vault_blocked))
(assert
 (= cbf01c716_vault_erc20_balance cbf01c716_vault_erc20_balance))
(define-fun report_preconditions () Bool (distinct 0 cbf01c716_vault_erc20_balance))
(define-fun report_safety () Bool (=> (distinct 0 cbf01c716_vault_erc20_balance)
    (not cbf01c716_unregister_vault_blocked)))
(define-fun report_effects () Bool (and (distinct 0 cbf01c716_vault_erc20_balance)
     cbf01c716_unregister_vault_blocked
     cbf01c716_unregister_vault_blocked
     cbf01c716_unregister_vault_blocked))
(assert report_preconditions)
(check-sat)
(get-model)
