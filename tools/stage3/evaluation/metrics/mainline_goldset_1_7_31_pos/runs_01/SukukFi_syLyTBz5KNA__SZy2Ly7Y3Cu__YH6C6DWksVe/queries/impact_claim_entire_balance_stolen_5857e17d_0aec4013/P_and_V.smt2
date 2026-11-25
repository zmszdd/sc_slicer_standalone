; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c5ebac1c8_caller_is_owner_or_has_owner_allowance () Bool)
(declare-fun c5ebac1c8_entire_vault_balance_stolen () Bool)
(declare-fun c5ebac1c8_owner_shares_burned () Bool)
(declare-fun c5ebac1c8_victim_self_allowance () Int)
(assert
 (= c5ebac1c8_caller_is_owner_or_has_owner_allowance c5ebac1c8_caller_is_owner_or_has_owner_allowance))
(assert
 (= c5ebac1c8_entire_vault_balance_stolen c5ebac1c8_entire_vault_balance_stolen))
(assert
 (= c5ebac1c8_owner_shares_burned c5ebac1c8_owner_shares_burned))
(assert
 (= c5ebac1c8_victim_self_allowance c5ebac1c8_victim_self_allowance))
(define-fun report_preconditions () Bool (= 100 c5ebac1c8_victim_self_allowance))
(define-fun report_safety () Bool (=> c5ebac1c8_owner_shares_burned
    c5ebac1c8_caller_is_owner_or_has_owner_allowance))
(define-fun report_effects () Bool (and c5ebac1c8_owner_shares_burned
     (not c5ebac1c8_caller_is_owner_or_has_owner_allowance)
     c5ebac1c8_entire_vault_balance_stolen
     c5ebac1c8_entire_vault_balance_stolen))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
