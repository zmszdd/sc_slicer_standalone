; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2eed0c4d_user_holds_shares () Bool)
(declare-fun c2eed0c4d_withdraw_all_shares () Bool)
(declare-fun c2eed0c4d_withdraw_completed () Bool)
(declare-fun c2eed0c4d_withdraw_reverted () Bool)
(declare-fun c2eed0c4d_zero_leg_present () Bool)
(assert
 (= c2eed0c4d_user_holds_shares c2eed0c4d_user_holds_shares))
(assert
 (= c2eed0c4d_withdraw_all_shares c2eed0c4d_withdraw_all_shares))
(assert
 (= c2eed0c4d_withdraw_completed c2eed0c4d_withdraw_completed))
(assert
 (= c2eed0c4d_withdraw_reverted c2eed0c4d_withdraw_reverted))
(assert
 (= c2eed0c4d_zero_leg_present c2eed0c4d_zero_leg_present))
(define-fun report_preconditions () Bool (and c2eed0c4d_user_holds_shares
     c2eed0c4d_withdraw_all_shares
     c2eed0c4d_zero_leg_present))
(define-fun report_safety () Bool (=> (and c2eed0c4d_user_holds_shares
         c2eed0c4d_withdraw_all_shares
         c2eed0c4d_zero_leg_present)
    (and c2eed0c4d_withdraw_completed (not c2eed0c4d_withdraw_reverted))))
(define-fun report_effects () Bool (and c2eed0c4d_user_holds_shares
     c2eed0c4d_withdraw_all_shares
     c2eed0c4d_zero_leg_present
     (not (and c2eed0c4d_withdraw_completed (not c2eed0c4d_withdraw_reverted)))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
