; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c04060cf9_bob_exits_without_fee () Bool)
(declare-fun c04060cf9_bob_pnl () Int)
(declare-fun c04060cf9_bob_positive_pnl () Bool)
(declare-fun c04060cf9_performance_fee_paid_on_exit () Bool)
(declare-fun c04060cf9_shares_transferable () Bool)
(assert
 (= c04060cf9_bob_exits_without_fee c04060cf9_bob_exits_without_fee))
(assert
 (= c04060cf9_bob_pnl c04060cf9_bob_pnl))
(assert
 (= c04060cf9_bob_positive_pnl c04060cf9_bob_positive_pnl))
(assert
 (= c04060cf9_performance_fee_paid_on_exit c04060cf9_performance_fee_paid_on_exit))
(assert
 (= c04060cf9_shares_transferable c04060cf9_shares_transferable))
(define-fun report_preconditions () Bool (and (< 0 c04060cf9_bob_pnl)
     c04060cf9_bob_positive_pnl
     c04060cf9_shares_transferable))
(define-fun report_safety () Bool (=> c04060cf9_bob_positive_pnl c04060cf9_performance_fee_paid_on_exit))
(define-fun report_effects () Bool (and c04060cf9_bob_positive_pnl
     (not c04060cf9_performance_fee_paid_on_exit)
     c04060cf9_bob_exits_without_fee
     c04060cf9_bob_exits_without_fee))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
