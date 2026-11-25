; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3d628e14_caller_is_owner_or_has_allowance () Bool)
(declare-fun c3d628e14_funds_stolen_from_self_allowance_user () Bool)
(declare-fun c3d628e14_victim_self_allowance_obtained () Bool)
(declare-fun c3d628e14_withdraw_on_behalf_of_owner () Bool)
(assert
 (= c3d628e14_caller_is_owner_or_has_allowance c3d628e14_caller_is_owner_or_has_allowance))
(assert
 (= c3d628e14_funds_stolen_from_self_allowance_user c3d628e14_funds_stolen_from_self_allowance_user))
(assert
 (= c3d628e14_victim_self_allowance_obtained c3d628e14_victim_self_allowance_obtained))
(assert
 (= c3d628e14_withdraw_on_behalf_of_owner c3d628e14_withdraw_on_behalf_of_owner))
(define-fun report_preconditions () Bool c3d628e14_victim_self_allowance_obtained)
(define-fun report_safety () Bool (=> c3d628e14_withdraw_on_behalf_of_owner
    c3d628e14_caller_is_owner_or_has_allowance))
(define-fun report_effects () Bool (and c3d628e14_withdraw_on_behalf_of_owner
     (not c3d628e14_caller_is_owner_or_has_allowance)
     c3d628e14_funds_stolen_from_self_allowance_user))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
