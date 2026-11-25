; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8a4f8d50_active_user_with_self_allowance () Bool)
(declare-fun c8a4f8d50_caller_is_owner_or_has_share_allowance () Bool)
(declare-fun c8a4f8d50_entire_balance_stolen_occurred () Bool)
(declare-fun c8a4f8d50_victim_self_allowance_obtained () Bool)
(declare-fun c8a4f8d50_withdraw_on_behalf_of_owner_executed () Bool)
(assert
 (= c8a4f8d50_active_user_with_self_allowance c8a4f8d50_active_user_with_self_allowance))
(assert
 (= c8a4f8d50_caller_is_owner_or_has_share_allowance c8a4f8d50_caller_is_owner_or_has_share_allowance))
(assert
 (= c8a4f8d50_entire_balance_stolen_occurred c8a4f8d50_entire_balance_stolen_occurred))
(assert
 (= c8a4f8d50_victim_self_allowance_obtained c8a4f8d50_victim_self_allowance_obtained))
(assert
 (= c8a4f8d50_withdraw_on_behalf_of_owner_executed c8a4f8d50_withdraw_on_behalf_of_owner_executed))
(define-fun report_preconditions () Bool c8a4f8d50_victim_self_allowance_obtained)
(define-fun report_safety () Bool (=> c8a4f8d50_withdraw_on_behalf_of_owner_executed
    c8a4f8d50_caller_is_owner_or_has_share_allowance))
(define-fun report_effects () Bool (and c8a4f8d50_withdraw_on_behalf_of_owner_executed
     (not c8a4f8d50_caller_is_owner_or_has_share_allowance)
     c8a4f8d50_active_user_with_self_allowance
     c8a4f8d50_entire_balance_stolen_occurred
     c8a4f8d50_active_user_with_self_allowance))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
