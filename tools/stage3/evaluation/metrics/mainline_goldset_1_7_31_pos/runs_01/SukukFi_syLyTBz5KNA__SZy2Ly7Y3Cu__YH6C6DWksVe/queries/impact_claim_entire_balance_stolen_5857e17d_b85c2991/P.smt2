; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb0cd0c4d_caller_has_owner_allowance () Bool)
(declare-fun cb0cd0c4d_caller_is_owner () Bool)
(declare-fun cb0cd0c4d_entire_vault_balance_stolen () Bool)
(declare-fun cb0cd0c4d_owner_shares_burned () Bool)
(declare-fun cb0cd0c4d_victim_self_allowance () Int)
(assert
 (= cb0cd0c4d_caller_has_owner_allowance cb0cd0c4d_caller_has_owner_allowance))
(assert
 (= cb0cd0c4d_caller_is_owner cb0cd0c4d_caller_is_owner))
(assert
 (= cb0cd0c4d_entire_vault_balance_stolen cb0cd0c4d_entire_vault_balance_stolen))
(assert
 (= cb0cd0c4d_owner_shares_burned cb0cd0c4d_owner_shares_burned))
(assert
 (= cb0cd0c4d_victim_self_allowance cb0cd0c4d_victim_self_allowance))
(define-fun report_preconditions () Bool (= 100 cb0cd0c4d_victim_self_allowance))
(define-fun report_safety () Bool (=> cb0cd0c4d_owner_shares_burned
    (or cb0cd0c4d_caller_is_owner cb0cd0c4d_caller_has_owner_allowance)))
(define-fun report_effects () Bool (and cb0cd0c4d_owner_shares_burned
     (not (or cb0cd0c4d_caller_is_owner cb0cd0c4d_caller_has_owner_allowance))
     cb0cd0c4d_entire_vault_balance_stolen
     cb0cd0c4d_entire_vault_balance_stolen))
(assert report_preconditions)
(check-sat)
(get-model)
