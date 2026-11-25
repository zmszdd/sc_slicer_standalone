; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7ca87762_assets_sent_to_attacker_amount () Int)
(declare-fun c7ca87762_caller_has_owner_allowance () Bool)
(declare-fun c7ca87762_caller_is_owner () Bool)
(declare-fun c7ca87762_owner_shares_burned () Bool)
(declare-fun c7ca87762_victim_assets_deposited () Int)
(declare-fun c7ca87762_victim_self_allowance () Int)
(declare-fun c7ca87762_victim_shares_received () Int)
(assert
 (= c7ca87762_assets_sent_to_attacker_amount c7ca87762_assets_sent_to_attacker_amount))
(assert
 (= c7ca87762_caller_has_owner_allowance c7ca87762_caller_has_owner_allowance))
(assert
 (= c7ca87762_caller_is_owner c7ca87762_caller_is_owner))
(assert
 (= c7ca87762_owner_shares_burned c7ca87762_owner_shares_burned))
(assert
 (= c7ca87762_victim_assets_deposited c7ca87762_victim_assets_deposited))
(assert
 (= c7ca87762_victim_self_allowance c7ca87762_victim_self_allowance))
(assert
 (= c7ca87762_victim_shares_received c7ca87762_victim_shares_received))
(define-fun report_preconditions () Bool (and (= 100 c7ca87762_victim_assets_deposited)
     (= 100 c7ca87762_victim_shares_received)
     (= 100 c7ca87762_victim_self_allowance)))
(define-fun report_safety () Bool (=> c7ca87762_owner_shares_burned
    (or c7ca87762_caller_is_owner c7ca87762_caller_has_owner_allowance)))
(define-fun report_effects () Bool (and c7ca87762_owner_shares_burned
     (not (or c7ca87762_caller_is_owner c7ca87762_caller_has_owner_allowance))
     (= 100 c7ca87762_assets_sent_to_attacker_amount)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
