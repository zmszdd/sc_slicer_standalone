; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun caa9d517d_caller_has_owner_allowance () Bool)
(declare-fun caa9d517d_caller_is_owner () Bool)
(declare-fun caa9d517d_shares_burned_from_owner () Bool)
(declare-fun caa9d517d_vault_balance_drained () Bool)
(declare-fun caa9d517d_victim_deposited_assets () Int)
(declare-fun caa9d517d_victim_received_shares () Int)
(declare-fun caa9d517d_victim_self_allowance () Int)
(assert
 (= caa9d517d_caller_has_owner_allowance caa9d517d_caller_has_owner_allowance))
(assert
 (= caa9d517d_caller_is_owner caa9d517d_caller_is_owner))
(assert
 (= caa9d517d_shares_burned_from_owner caa9d517d_shares_burned_from_owner))
(assert
 (= caa9d517d_vault_balance_drained caa9d517d_vault_balance_drained))
(assert
 (= caa9d517d_victim_deposited_assets caa9d517d_victim_deposited_assets))
(assert
 (= caa9d517d_victim_received_shares caa9d517d_victim_received_shares))
(assert
 (= caa9d517d_victim_self_allowance caa9d517d_victim_self_allowance))
(define-fun report_preconditions () Bool (and (= 100 caa9d517d_victim_deposited_assets)
     (= 100 caa9d517d_victim_received_shares)
     (= 100 caa9d517d_victim_self_allowance)))
(define-fun report_safety () Bool (=> caa9d517d_shares_burned_from_owner
    (or caa9d517d_caller_is_owner caa9d517d_caller_has_owner_allowance)))
(define-fun report_effects () Bool (and caa9d517d_shares_burned_from_owner
     (not (or caa9d517d_caller_is_owner caa9d517d_caller_has_owner_allowance))
     caa9d517d_shares_burned_from_owner
     caa9d517d_vault_balance_drained
     caa9d517d_vault_balance_drained))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
