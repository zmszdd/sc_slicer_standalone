; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce0066556_balance_check_enforced_only_outermost () Bool)
(declare-fun ce0066556_inner_forwards_no_eth () Bool)
(declare-fun ce0066556_inner_multicall_nested_occurred () Bool)
(declare-fun ce0066556_nested_multicall_reverted () Bool)
(declare-fun ce0066556_outer_msg_value_nonzero () Bool)
(assert
 (= ce0066556_balance_check_enforced_only_outermost ce0066556_balance_check_enforced_only_outermost))
(assert
 (= ce0066556_inner_forwards_no_eth ce0066556_inner_forwards_no_eth))
(assert
 (= ce0066556_inner_multicall_nested_occurred ce0066556_inner_multicall_nested_occurred))
(assert
 (= ce0066556_nested_multicall_reverted ce0066556_nested_multicall_reverted))
(assert
 (= ce0066556_outer_msg_value_nonzero ce0066556_outer_msg_value_nonzero))
(define-fun report_preconditions () Bool (and ce0066556_outer_msg_value_nonzero
     ce0066556_inner_multicall_nested_occurred
     ce0066556_inner_forwards_no_eth))
(define-fun report_safety () Bool (=> ce0066556_balance_check_enforced_only_outermost
    (not ce0066556_nested_multicall_reverted)))
(define-fun report_effects () Bool ce0066556_nested_multicall_reverted)
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
