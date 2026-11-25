; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1888a122_bob_pnl_before_exit () Int)
(declare-fun c1888a122_fabricated_nonpositive_pnl () Bool)
(declare-fun c1888a122_performance_fee_bypassed () Bool)
(declare-fun c1888a122_performance_fee_paid_on_exit () Bool)
(declare-fun c1888a122_shares_transferable () Bool)
(assert
 (= c1888a122_bob_pnl_before_exit c1888a122_bob_pnl_before_exit))
(assert
 (= c1888a122_fabricated_nonpositive_pnl c1888a122_fabricated_nonpositive_pnl))
(assert
 (= c1888a122_performance_fee_bypassed c1888a122_performance_fee_bypassed))
(assert
 (= c1888a122_performance_fee_paid_on_exit c1888a122_performance_fee_paid_on_exit))
(assert
 (= c1888a122_shares_transferable c1888a122_shares_transferable))
(define-fun report_preconditions () Bool (and (< 0 c1888a122_bob_pnl_before_exit) c1888a122_shares_transferable))
(define-fun report_safety () Bool (=> (< 0 c1888a122_bob_pnl_before_exit) c1888a122_performance_fee_paid_on_exit))
(define-fun report_effects () Bool (and (< 0 c1888a122_bob_pnl_before_exit)
     (not c1888a122_performance_fee_paid_on_exit)
     c1888a122_fabricated_nonpositive_pnl
     c1888a122_performance_fee_bypassed))
