; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun total_fee_share_zero () Bool)
(declare-fun pair_absent () Bool)
(declare-fun total_shares_zero () Bool)
(declare-fun all_participants_exited () Bool)
(declare-fun amm_trading_fails () Bool)
(assert
 (= total_fee_share_zero total_fee_share_zero))
(assert
 (= pair_absent pair_absent))
(assert
 (= total_shares_zero total_shares_zero))
(assert
 (= all_participants_exited all_participants_exited))
(assert
 (= amm_trading_fails amm_trading_fails))
(define-fun report_preconditions () Bool (and total_fee_share_zero pair_absent total_shares_zero all_participants_exited))
(define-fun report_safety () Bool (=> (and total_fee_share_zero pair_absent) (not amm_trading_fails)))
(define-fun report_effects () Bool (and total_fee_share_zero pair_absent amm_trading_fails))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
