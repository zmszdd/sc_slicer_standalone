; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2eed0c4d_remaining_amount () Int)
(declare-fun c2eed0c4d_user_holds_shares () Bool)
(declare-fun c2eed0c4d_withdraw_all_shares () Bool)
(declare-fun c2eed0c4d_withdraw_reverts () Bool)
(assert
 (= c2eed0c4d_remaining_amount c2eed0c4d_remaining_amount))
(assert
 (= c2eed0c4d_user_holds_shares c2eed0c4d_user_holds_shares))
(assert
 (= c2eed0c4d_withdraw_all_shares c2eed0c4d_withdraw_all_shares))
(assert
 (= c2eed0c4d_withdraw_reverts c2eed0c4d_withdraw_reverts))
(define-fun report_preconditions () Bool (and c2eed0c4d_user_holds_shares
     c2eed0c4d_withdraw_all_shares
     (= 0 c2eed0c4d_remaining_amount)))
(define-fun report_safety () Bool (=> (and c2eed0c4d_user_holds_shares
         c2eed0c4d_withdraw_all_shares
         (= 0 c2eed0c4d_remaining_amount))
    (not c2eed0c4d_withdraw_reverts)))
(define-fun report_effects () Bool (and c2eed0c4d_user_holds_shares
     c2eed0c4d_withdraw_all_shares
     (= 0 c2eed0c4d_remaining_amount)
     (not (not c2eed0c4d_withdraw_reverts))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
