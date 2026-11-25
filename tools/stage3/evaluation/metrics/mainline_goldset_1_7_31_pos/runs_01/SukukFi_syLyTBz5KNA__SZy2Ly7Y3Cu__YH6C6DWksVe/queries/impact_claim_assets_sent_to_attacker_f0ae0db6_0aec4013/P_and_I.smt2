; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7e3b7b93_assets_sent_to_attacker_amount () Int)
(declare-fun c7e3b7b93_caller_is_owner_or_has_owner_allowance () Bool)
(declare-fun c7e3b7b93_owner_shares_burned () Bool)
(declare-fun c7e3b7b93_victim_deposited_assets () Int)
(declare-fun c7e3b7b93_victim_received_shares () Int)
(declare-fun c7e3b7b93_victim_self_allowance () Int)
(assert
 (= c7e3b7b93_assets_sent_to_attacker_amount c7e3b7b93_assets_sent_to_attacker_amount))
(assert
 (= c7e3b7b93_caller_is_owner_or_has_owner_allowance c7e3b7b93_caller_is_owner_or_has_owner_allowance))
(assert
 (= c7e3b7b93_owner_shares_burned c7e3b7b93_owner_shares_burned))
(assert
 (= c7e3b7b93_victim_deposited_assets c7e3b7b93_victim_deposited_assets))
(assert
 (= c7e3b7b93_victim_received_shares c7e3b7b93_victim_received_shares))
(assert
 (= c7e3b7b93_victim_self_allowance c7e3b7b93_victim_self_allowance))
(define-fun report_preconditions () Bool (and (= 100 c7e3b7b93_victim_deposited_assets)
     (= 100 c7e3b7b93_victim_received_shares)
     (= 100 c7e3b7b93_victim_self_allowance)))
(define-fun report_safety () Bool (=> c7e3b7b93_owner_shares_burned
    c7e3b7b93_caller_is_owner_or_has_owner_allowance))
(define-fun report_effects () Bool (and c7e3b7b93_owner_shares_burned
     (not c7e3b7b93_caller_is_owner_or_has_owner_allowance)
     (= 100 c7e3b7b93_assets_sent_to_attacker_amount)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
