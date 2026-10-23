; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1c31579e_cannot_exit_self_dos () Bool)
(declare-fun c1c31579e_user_holds_ghybr_shares () Bool)
(declare-fun c1c31579e_withdraw_all_shares () Bool)
(declare-fun c1c31579e_withdraw_succeeds () Bool)
(declare-fun c1c31579e_zero_leg_present () Bool)
(assert
 (= c1c31579e_cannot_exit_self_dos c1c31579e_cannot_exit_self_dos))
(assert
 (= c1c31579e_user_holds_ghybr_shares c1c31579e_user_holds_ghybr_shares))
(assert
 (= c1c31579e_withdraw_all_shares c1c31579e_withdraw_all_shares))
(assert
 (= c1c31579e_withdraw_succeeds c1c31579e_withdraw_succeeds))
(assert
 (= c1c31579e_zero_leg_present c1c31579e_zero_leg_present))
(define-fun report_preconditions () Bool (and c1c31579e_user_holds_ghybr_shares
     c1c31579e_withdraw_all_shares
     c1c31579e_zero_leg_present))
(define-fun report_safety () Bool (=> (and c1c31579e_user_holds_ghybr_shares
         c1c31579e_withdraw_all_shares
         c1c31579e_zero_leg_present)
    (and c1c31579e_withdraw_succeeds (not c1c31579e_cannot_exit_self_dos))))
(define-fun report_effects () Bool (and c1c31579e_user_holds_ghybr_shares
     c1c31579e_withdraw_all_shares
     c1c31579e_zero_leg_present
     (not (and c1c31579e_withdraw_succeeds (not c1c31579e_cannot_exit_self_dos)))))
