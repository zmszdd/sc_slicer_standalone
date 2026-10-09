; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun fork_reserve_update_reduced () Bool)
(declare-fun lp_portfolio_fork () Int)
(declare-fun lp_portfolio_reference () Int)
(declare-fun identical_swap_performed () Bool)
(assert
 (= fork_reserve_update_reduced fork_reserve_update_reduced))
(assert
 (= lp_portfolio_fork lp_portfolio_fork))
(assert
 (= lp_portfolio_reference lp_portfolio_reference))
(assert
 (= identical_swap_performed identical_swap_performed))
(define-fun report_preconditions () Bool (and fork_reserve_update_reduced identical_swap_performed))
(define-fun report_safety () Bool (=> identical_swap_performed (>= lp_portfolio_fork lp_portfolio_reference)))
(define-fun report_effects () Bool (and identical_swap_performed
     (not (>= lp_portfolio_fork lp_portfolio_reference))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
