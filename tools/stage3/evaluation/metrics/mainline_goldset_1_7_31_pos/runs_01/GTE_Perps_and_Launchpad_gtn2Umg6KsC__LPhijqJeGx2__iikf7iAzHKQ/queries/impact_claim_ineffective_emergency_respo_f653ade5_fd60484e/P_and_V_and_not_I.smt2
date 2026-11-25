; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc93dc2c5_clearing_house_active () Bool)
(declare-fun cc93dc2c5_deposit_withdraw_blocked () Bool)
(declare-fun cc93dc2c5_fund_ops_proceed_during_pause () Bool)
(declare-fun cc93dc2c5_trading_reverts_when_paused () Bool)
(assert
 (= cc93dc2c5_clearing_house_active cc93dc2c5_clearing_house_active))
(assert
 (= cc93dc2c5_deposit_withdraw_blocked cc93dc2c5_deposit_withdraw_blocked))
(assert
 (= cc93dc2c5_fund_ops_proceed_during_pause cc93dc2c5_fund_ops_proceed_during_pause))
(assert
 (= cc93dc2c5_trading_reverts_when_paused cc93dc2c5_trading_reverts_when_paused))
(define-fun report_preconditions () Bool (and (= cc93dc2c5_clearing_house_active false)
     cc93dc2c5_trading_reverts_when_paused))
(define-fun report_safety () Bool (=> cc93dc2c5_fund_ops_proceed_during_pause cc93dc2c5_deposit_withdraw_blocked))
(define-fun report_effects () Bool (and cc93dc2c5_fund_ops_proceed_during_pause
     (not cc93dc2c5_deposit_withdraw_blocked)
     cc93dc2c5_fund_ops_proceed_during_pause))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
