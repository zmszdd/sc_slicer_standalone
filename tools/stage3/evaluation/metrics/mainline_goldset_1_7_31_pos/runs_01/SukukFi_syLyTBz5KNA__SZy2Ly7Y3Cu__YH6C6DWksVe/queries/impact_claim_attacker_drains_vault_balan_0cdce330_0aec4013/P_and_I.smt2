; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce1735bbb_attacker_received_assets () Bool)
(declare-fun ce1735bbb_caller_is_owner_or_has_allowance () Bool)
(declare-fun ce1735bbb_owner_shares_burned () Bool)
(declare-fun ce1735bbb_victim_assets_deposited () Int)
(declare-fun ce1735bbb_victim_self_allowance () Int)
(declare-fun ce1735bbb_victim_shares_received () Int)
(assert
 (= ce1735bbb_attacker_received_assets ce1735bbb_attacker_received_assets))
(assert
 (= ce1735bbb_caller_is_owner_or_has_allowance ce1735bbb_caller_is_owner_or_has_allowance))
(assert
 (= ce1735bbb_owner_shares_burned ce1735bbb_owner_shares_burned))
(assert
 (= ce1735bbb_victim_assets_deposited ce1735bbb_victim_assets_deposited))
(assert
 (= ce1735bbb_victim_self_allowance ce1735bbb_victim_self_allowance))
(assert
 (= ce1735bbb_victim_shares_received ce1735bbb_victim_shares_received))
(define-fun report_preconditions () Bool (and (= 100 ce1735bbb_victim_assets_deposited)
     (= 100 ce1735bbb_victim_shares_received)
     (= 100 ce1735bbb_victim_self_allowance)))
(define-fun report_safety () Bool (=> ce1735bbb_owner_shares_burned ce1735bbb_caller_is_owner_or_has_allowance))
(define-fun report_effects () Bool (and ce1735bbb_owner_shares_burned
     (not ce1735bbb_caller_is_owner_or_has_allowance)
     ce1735bbb_attacker_received_assets
     ce1735bbb_owner_shares_burned
     ce1735bbb_attacker_received_assets))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
