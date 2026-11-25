; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3db84b6d_caller_is_owner_or_allowee () Bool)
(declare-fun c3db84b6d_shares_burned () Bool)
(declare-fun c3db84b6d_victim_self_allowance () Int)
(declare-fun c3db84b6d_victim_share_balance_before () Int)
(declare-fun c3db84b6d_victim_shares_burned_amount () Int)
(assert
 (= c3db84b6d_caller_is_owner_or_allowee c3db84b6d_caller_is_owner_or_allowee))
(assert
 (= c3db84b6d_shares_burned c3db84b6d_shares_burned))
(assert
 (= c3db84b6d_victim_self_allowance c3db84b6d_victim_self_allowance))
(assert
 (= c3db84b6d_victim_share_balance_before c3db84b6d_victim_share_balance_before))
(assert
 (= c3db84b6d_victim_shares_burned_amount c3db84b6d_victim_shares_burned_amount))
(define-fun report_preconditions () Bool (and (= 100 c3db84b6d_victim_share_balance_before)
     (= 100 c3db84b6d_victim_self_allowance)))
(define-fun report_safety () Bool (=> c3db84b6d_shares_burned c3db84b6d_caller_is_owner_or_allowee))
(define-fun report_effects () Bool (and c3db84b6d_shares_burned
     (not c3db84b6d_caller_is_owner_or_allowee)
     c3db84b6d_shares_burned
     (= 100 c3db84b6d_victim_shares_burned_amount)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
