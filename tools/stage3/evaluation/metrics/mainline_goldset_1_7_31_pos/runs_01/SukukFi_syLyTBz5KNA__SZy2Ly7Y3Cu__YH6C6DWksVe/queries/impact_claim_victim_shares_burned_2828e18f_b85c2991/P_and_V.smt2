; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c125d8910_caller_has_owner_allowance () Bool)
(declare-fun c125d8910_caller_is_owner () Bool)
(declare-fun c125d8910_victim_self_allowance () Int)
(declare-fun c125d8910_victim_shares_balance () Int)
(declare-fun c125d8910_victim_shares_burned_amount () Int)
(assert
 (= c125d8910_caller_has_owner_allowance c125d8910_caller_has_owner_allowance))
(assert
 (= c125d8910_caller_is_owner c125d8910_caller_is_owner))
(assert
 (= c125d8910_victim_self_allowance c125d8910_victim_self_allowance))
(assert
 (= c125d8910_victim_shares_balance c125d8910_victim_shares_balance))
(assert
 (= c125d8910_victim_shares_burned_amount c125d8910_victim_shares_burned_amount))
(define-fun report_preconditions () Bool (and (= 100 c125d8910_victim_shares_balance)
     (= 100 c125d8910_victim_self_allowance)))
(define-fun report_safety () Bool (=> (< 0 c125d8910_victim_shares_burned_amount)
    (or c125d8910_caller_is_owner c125d8910_caller_has_owner_allowance)))
(define-fun report_effects () Bool (and (< 0 c125d8910_victim_shares_burned_amount)
     (not (or c125d8910_caller_is_owner c125d8910_caller_has_owner_allowance))
     (= 100 c125d8910_victim_shares_burned_amount)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
