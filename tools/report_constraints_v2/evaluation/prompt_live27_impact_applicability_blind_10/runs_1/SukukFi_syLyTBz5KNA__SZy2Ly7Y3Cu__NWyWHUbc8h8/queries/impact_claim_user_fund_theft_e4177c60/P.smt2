; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1ab855da_attacker_is_owner_or_operator () Bool)
(declare-fun c1ab855da_attacker_received_assets () Bool)
(declare-fun c1ab855da_victim_self_allowance_amount () Int)
(declare-fun c1ab855da_victim_vault_share_balance () Int)
(declare-fun c1ab855da_withdraw_authorized_by_owner_or_operator () Bool)
(assert
 (= c1ab855da_attacker_is_owner_or_operator c1ab855da_attacker_is_owner_or_operator))
(assert
 (= c1ab855da_attacker_received_assets c1ab855da_attacker_received_assets))
(assert
 (= c1ab855da_victim_self_allowance_amount c1ab855da_victim_self_allowance_amount))
(assert
 (= c1ab855da_victim_vault_share_balance c1ab855da_victim_vault_share_balance))
(assert
 (= c1ab855da_withdraw_authorized_by_owner_or_operator c1ab855da_withdraw_authorized_by_owner_or_operator))
(define-fun report_preconditions () Bool (and (< 0 c1ab855da_victim_vault_share_balance)
     (< 0 c1ab855da_victim_self_allowance_amount)
     (not c1ab855da_attacker_is_owner_or_operator)))
(define-fun report_safety () Bool (=> c1ab855da_attacker_received_assets
    (=> c1ab855da_attacker_received_assets
        c1ab855da_withdraw_authorized_by_owner_or_operator)))
(define-fun report_effects () Bool (and c1ab855da_attacker_received_assets
     c1ab855da_attacker_received_assets
     (not c1ab855da_withdraw_authorized_by_owner_or_operator)))
(assert report_preconditions)
(check-sat)
(get-model)
