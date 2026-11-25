; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8f9c450a_caller_is_owner_or_has_share_allowance () Bool)
(declare-fun c8f9c450a_victim_funds_lost_attacker_received () Bool)
(declare-fun c8f9c450a_victim_self_allowance_obtained () Bool)
(declare-fun c8f9c450a_withdraw_on_behalf_of_owner_executed () Bool)
(assert
 (= c8f9c450a_caller_is_owner_or_has_share_allowance c8f9c450a_caller_is_owner_or_has_share_allowance))
(assert
 (= c8f9c450a_victim_funds_lost_attacker_received c8f9c450a_victim_funds_lost_attacker_received))
(assert
 (= c8f9c450a_victim_self_allowance_obtained c8f9c450a_victim_self_allowance_obtained))
(assert
 (= c8f9c450a_withdraw_on_behalf_of_owner_executed c8f9c450a_withdraw_on_behalf_of_owner_executed))
(define-fun report_preconditions () Bool c8f9c450a_victim_self_allowance_obtained)
(define-fun report_safety () Bool (=> c8f9c450a_withdraw_on_behalf_of_owner_executed
    c8f9c450a_caller_is_owner_or_has_share_allowance))
(define-fun report_effects () Bool (and c8f9c450a_withdraw_on_behalf_of_owner_executed
     (not c8f9c450a_caller_is_owner_or_has_share_allowance)
     c8f9c450a_victim_funds_lost_attacker_received
     c8f9c450a_victim_funds_lost_attacker_received))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
