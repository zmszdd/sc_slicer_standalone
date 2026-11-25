; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c84729550_bob_pnl () Int)
(declare-fun c84729550_bob_positive_pnl () Bool)
(declare-fun c84729550_fee_bypass_occurred () Bool)
(declare-fun c84729550_fee_bypass_unfair () Bool)
(declare-fun c84729550_performance_fee_paid_on_exit () Bool)
(declare-fun c84729550_shares_transferable () Bool)
(assert
 (= c84729550_bob_pnl c84729550_bob_pnl))
(assert
 (= c84729550_bob_positive_pnl c84729550_bob_positive_pnl))
(assert
 (= c84729550_fee_bypass_occurred c84729550_fee_bypass_occurred))
(assert
 (= c84729550_fee_bypass_unfair c84729550_fee_bypass_unfair))
(assert
 (= c84729550_performance_fee_paid_on_exit c84729550_performance_fee_paid_on_exit))
(assert
 (= c84729550_shares_transferable c84729550_shares_transferable))
(define-fun report_preconditions () Bool (and (< 0 c84729550_bob_pnl)
     c84729550_bob_positive_pnl
     c84729550_shares_transferable))
(define-fun report_safety () Bool (=> (= c84729550_bob_pnl (- 20 18))
    (=> c84729550_bob_positive_pnl c84729550_performance_fee_paid_on_exit)))
(define-fun report_effects () Bool (and (= c84729550_bob_pnl (- 20 18))
     c84729550_bob_positive_pnl
     (not c84729550_performance_fee_paid_on_exit)
     (and c84729550_fee_bypass_occurred c84729550_fee_bypass_unfair)
     (and c84729550_fee_bypass_occurred c84729550_fee_bypass_unfair)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
