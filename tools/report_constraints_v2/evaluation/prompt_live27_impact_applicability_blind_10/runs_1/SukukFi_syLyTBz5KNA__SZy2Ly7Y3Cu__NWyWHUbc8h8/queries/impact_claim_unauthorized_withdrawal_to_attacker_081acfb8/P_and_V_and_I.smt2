; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cf34f3f50_attacker_is_owner_or_operator () Bool)
(declare-fun cf34f3f50_victim_self_allowance () Int)
(declare-fun cf34f3f50_victim_share_balance () Int)
(declare-fun cf34f3f50_withdrawal_succeeds_to_attacker () Bool)
(assert
 (= cf34f3f50_attacker_is_owner_or_operator cf34f3f50_attacker_is_owner_or_operator))
(assert
 (= cf34f3f50_victim_self_allowance cf34f3f50_victim_self_allowance))
(assert
 (= cf34f3f50_victim_share_balance cf34f3f50_victim_share_balance))
(assert
 (= cf34f3f50_withdrawal_succeeds_to_attacker cf34f3f50_withdrawal_succeeds_to_attacker))
(define-fun report_preconditions () Bool (and (< 0 cf34f3f50_victim_share_balance)
     (< 0 cf34f3f50_victim_self_allowance)
     (not cf34f3f50_attacker_is_owner_or_operator)))
(define-fun report_safety () Bool (=> cf34f3f50_withdrawal_succeeds_to_attacker
    (=> cf34f3f50_withdrawal_succeeds_to_attacker
        cf34f3f50_attacker_is_owner_or_operator)))
(define-fun report_effects () Bool (and cf34f3f50_withdrawal_succeeds_to_attacker
     cf34f3f50_withdrawal_succeeds_to_attacker
     (not cf34f3f50_attacker_is_owner_or_operator)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
