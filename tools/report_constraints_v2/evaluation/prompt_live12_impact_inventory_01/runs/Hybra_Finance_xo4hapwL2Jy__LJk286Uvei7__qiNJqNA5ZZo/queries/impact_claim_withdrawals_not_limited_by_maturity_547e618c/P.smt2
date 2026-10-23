; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c38314bd6_maturity_time_at_deposit () Int)
(declare-fun c38314bd6_withdrawal_limited_by_maturity () Bool)
(assert
 (= c38314bd6_maturity_time_at_deposit c38314bd6_maturity_time_at_deposit))
(assert
 (= c38314bd6_withdrawal_limited_by_maturity c38314bd6_withdrawal_limited_by_maturity))
(define-fun report_preconditions () Bool (= 0 c38314bd6_maturity_time_at_deposit))
(define-fun report_safety () Bool (=> (= 0 c38314bd6_maturity_time_at_deposit)
    c38314bd6_withdrawal_limited_by_maturity))
(define-fun report_effects () Bool (and (= 0 c38314bd6_maturity_time_at_deposit)
     (not c38314bd6_withdrawal_limited_by_maturity)))
(assert report_preconditions)
(check-sat)
(get-model)
