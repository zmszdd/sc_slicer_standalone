; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6b29f17c_clearing_house_active () Bool)
(declare-fun c6b29f17c_deposit_withdraw_operation () Bool)
(declare-fun c6b29f17c_fund_ops_blocked_when_paused () Bool)
(declare-fun c6b29f17c_new_deposit_lost () Bool)
(assert
 (= c6b29f17c_clearing_house_active c6b29f17c_clearing_house_active))
(assert
 (= c6b29f17c_deposit_withdraw_operation c6b29f17c_deposit_withdraw_operation))
(assert
 (= c6b29f17c_fund_ops_blocked_when_paused c6b29f17c_fund_ops_blocked_when_paused))
(assert
 (= c6b29f17c_new_deposit_lost c6b29f17c_new_deposit_lost))
(define-fun report_preconditions () Bool (= c6b29f17c_clearing_house_active false))
(define-fun report_safety () Bool (=> c6b29f17c_deposit_withdraw_operation c6b29f17c_fund_ops_blocked_when_paused))
(define-fun report_effects () Bool (and c6b29f17c_deposit_withdraw_operation
     (not c6b29f17c_fund_ops_blocked_when_paused)
     c6b29f17c_new_deposit_lost
     c6b29f17c_new_deposit_lost))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
