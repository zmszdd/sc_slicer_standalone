; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbb173e17_attacker_received_assets () Bool)
(declare-fun cbb173e17_caller_is_owner_or_has_owner_allowance () Bool)
(declare-fun cbb173e17_owner_shares_burned () Bool)
(declare-fun cbb173e17_victim_deposited_assets () Int)
(declare-fun cbb173e17_victim_received_shares () Int)
(declare-fun cbb173e17_victim_self_allowance () Int)
(assert
 (= cbb173e17_attacker_received_assets cbb173e17_attacker_received_assets))
(assert
 (= cbb173e17_caller_is_owner_or_has_owner_allowance cbb173e17_caller_is_owner_or_has_owner_allowance))
(assert
 (= cbb173e17_owner_shares_burned cbb173e17_owner_shares_burned))
(assert
 (= cbb173e17_victim_deposited_assets cbb173e17_victim_deposited_assets))
(assert
 (= cbb173e17_victim_received_shares cbb173e17_victim_received_shares))
(assert
 (= cbb173e17_victim_self_allowance cbb173e17_victim_self_allowance))
(define-fun report_preconditions () Bool (and (= 100 cbb173e17_victim_deposited_assets)
     (= 100 cbb173e17_victim_received_shares)
     (= 100 cbb173e17_victim_self_allowance)))
(define-fun report_safety () Bool (=> cbb173e17_owner_shares_burned
    cbb173e17_caller_is_owner_or_has_owner_allowance))
(define-fun report_effects () Bool (and cbb173e17_owner_shares_burned
     (not cbb173e17_caller_is_owner_or_has_owner_allowance)
     cbb173e17_attacker_received_assets
     cbb173e17_owner_shares_burned
     cbb173e17_owner_shares_burned))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
