; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun reserve_update_fee_shaved () Bool)
(declare-fun swap_executed () Bool)
(declare-fun post_swap_reserves_consistent () Bool)
(declare-fun lp_portfolio_declines_more_than_reference () Bool)
(assert
 (= reserve_update_fee_shaved reserve_update_fee_shaved))
(assert
 (= swap_executed swap_executed))
(assert
 (= post_swap_reserves_consistent post_swap_reserves_consistent))
(assert
 (= lp_portfolio_declines_more_than_reference lp_portfolio_declines_more_than_reference))
(define-fun report_preconditions () Bool (and reserve_update_fee_shaved swap_executed))
(define-fun report_safety () Bool (=> (and reserve_update_fee_shaved swap_executed) post_swap_reserves_consistent))
(define-fun report_effects () Bool (and reserve_update_fee_shaved
     swap_executed
     (not post_swap_reserves_consistent)))
(assert report_preconditions)
(check-sat)
(get-model)
