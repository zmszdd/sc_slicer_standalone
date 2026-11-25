; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c27f81924_clearing_house_active () Bool)
(declare-fun c27f81924_fund_movement_occurs_during_pause () Bool)
(declare-fun c27f81924_fund_moving_ops_blocked_during_pause () Bool)
(declare-fun c27f81924_trading_ops_revert_protocol_not_active () Bool)
(assert
 (= c27f81924_clearing_house_active c27f81924_clearing_house_active))
(assert
 (= c27f81924_fund_movement_occurs_during_pause c27f81924_fund_movement_occurs_during_pause))
(assert
 (= c27f81924_fund_moving_ops_blocked_during_pause c27f81924_fund_moving_ops_blocked_during_pause))
(assert
 (= c27f81924_trading_ops_revert_protocol_not_active c27f81924_trading_ops_revert_protocol_not_active))
(define-fun report_preconditions () Bool (and (= c27f81924_clearing_house_active false)
     c27f81924_trading_ops_revert_protocol_not_active))
(define-fun report_safety () Bool (=> (= c27f81924_clearing_house_active false)
    c27f81924_fund_moving_ops_blocked_during_pause))
(define-fun report_effects () Bool (and (= c27f81924_clearing_house_active false)
     (not c27f81924_fund_moving_ops_blocked_during_pause)
     c27f81924_fund_movement_occurs_during_pause))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
