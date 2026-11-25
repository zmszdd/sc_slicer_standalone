; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c82a75a26_attacker_received_assets () Bool)
(declare-fun c82a75a26_caller_has_owner_allowance () Bool)
(declare-fun c82a75a26_caller_is_owner () Bool)
(declare-fun c82a75a26_shares_burned () Bool)
(declare-fun c82a75a26_victim_deposited_assets () Int)
(declare-fun c82a75a26_victim_received_shares () Int)
(declare-fun c82a75a26_victim_self_allowance () Int)
(assert
 (= c82a75a26_attacker_received_assets c82a75a26_attacker_received_assets))
(assert
 (= c82a75a26_caller_has_owner_allowance c82a75a26_caller_has_owner_allowance))
(assert
 (= c82a75a26_caller_is_owner c82a75a26_caller_is_owner))
(assert
 (= c82a75a26_shares_burned c82a75a26_shares_burned))
(assert
 (= c82a75a26_victim_deposited_assets c82a75a26_victim_deposited_assets))
(assert
 (= c82a75a26_victim_received_shares c82a75a26_victim_received_shares))
(assert
 (= c82a75a26_victim_self_allowance c82a75a26_victim_self_allowance))
(define-fun report_preconditions () Bool (and (= 100 c82a75a26_victim_deposited_assets)
     (= 100 c82a75a26_victim_received_shares)
     (= 100 c82a75a26_victim_self_allowance)))
(define-fun report_safety () Bool (=> c82a75a26_shares_burned
    (or c82a75a26_caller_is_owner c82a75a26_caller_has_owner_allowance)))
(define-fun report_effects () Bool (and c82a75a26_shares_burned
     (not (or c82a75a26_caller_is_owner c82a75a26_caller_has_owner_allowance))
     c82a75a26_attacker_received_assets
     c82a75a26_shares_burned
     c82a75a26_shares_burned))
