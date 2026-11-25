; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca8da65b7_caller_is_owner_or_has_share_allowance () Bool)
(declare-fun ca8da65b7_complete_loss_of_funds_occurred () Bool)
(declare-fun ca8da65b7_victim_has_self_allowance_obtained () Bool)
(declare-fun ca8da65b7_withdraw_on_behalf_of_owner_executed () Bool)
(assert
 (= ca8da65b7_caller_is_owner_or_has_share_allowance ca8da65b7_caller_is_owner_or_has_share_allowance))
(assert
 (= ca8da65b7_complete_loss_of_funds_occurred ca8da65b7_complete_loss_of_funds_occurred))
(assert
 (= ca8da65b7_victim_has_self_allowance_obtained ca8da65b7_victim_has_self_allowance_obtained))
(assert
 (= ca8da65b7_withdraw_on_behalf_of_owner_executed ca8da65b7_withdraw_on_behalf_of_owner_executed))
(define-fun report_preconditions () Bool ca8da65b7_victim_has_self_allowance_obtained)
(define-fun report_safety () Bool (=> ca8da65b7_withdraw_on_behalf_of_owner_executed
    ca8da65b7_caller_is_owner_or_has_share_allowance))
(define-fun report_effects () Bool (and ca8da65b7_withdraw_on_behalf_of_owner_executed
     (not ca8da65b7_caller_is_owner_or_has_share_allowance)
     ca8da65b7_complete_loss_of_funds_occurred
     ca8da65b7_victim_has_self_allowance_obtained))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
