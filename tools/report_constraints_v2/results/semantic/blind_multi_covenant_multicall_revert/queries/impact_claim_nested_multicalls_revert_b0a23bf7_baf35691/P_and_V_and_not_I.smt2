; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c40dd2d7d_inner_forwards_no_eth () Bool)
(declare-fun c40dd2d7d_inner_multicall_nested_occurs () Bool)
(declare-fun c40dd2d7d_nested_multicall_completes () Bool)
(declare-fun c40dd2d7d_nested_multicalls_revert_occurs () Bool)
(declare-fun c40dd2d7d_outer_msg_value_nonzero () Bool)
(assert
 (= c40dd2d7d_inner_forwards_no_eth c40dd2d7d_inner_forwards_no_eth))
(assert
 (= c40dd2d7d_inner_multicall_nested_occurs c40dd2d7d_inner_multicall_nested_occurs))
(assert
 (= c40dd2d7d_nested_multicall_completes c40dd2d7d_nested_multicall_completes))
(assert
 (= c40dd2d7d_nested_multicalls_revert_occurs c40dd2d7d_nested_multicalls_revert_occurs))
(assert
 (= c40dd2d7d_outer_msg_value_nonzero c40dd2d7d_outer_msg_value_nonzero))
(define-fun report_preconditions () Bool (and c40dd2d7d_outer_msg_value_nonzero
     c40dd2d7d_inner_multicall_nested_occurs
     c40dd2d7d_inner_forwards_no_eth))
(define-fun report_safety () Bool (=> (and c40dd2d7d_outer_msg_value_nonzero
         c40dd2d7d_inner_multicall_nested_occurs
         c40dd2d7d_inner_forwards_no_eth)
    c40dd2d7d_nested_multicall_completes))
(define-fun report_effects () Bool c40dd2d7d_nested_multicalls_revert_occurs)
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
