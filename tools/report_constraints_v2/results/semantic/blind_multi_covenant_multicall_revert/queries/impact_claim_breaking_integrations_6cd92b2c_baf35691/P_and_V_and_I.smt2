; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbe382308_inner_forwards_no_eth () Bool)
(declare-fun cbe382308_inner_multicall_nested_via_delegatecall () Bool)
(declare-fun cbe382308_integrations_broken () Bool)
(declare-fun cbe382308_nested_multicall_completes () Bool)
(declare-fun cbe382308_outer_msg_value_nonzero () Bool)
(assert
 (= cbe382308_inner_forwards_no_eth cbe382308_inner_forwards_no_eth))
(assert
 (= cbe382308_inner_multicall_nested_via_delegatecall cbe382308_inner_multicall_nested_via_delegatecall))
(assert
 (= cbe382308_integrations_broken cbe382308_integrations_broken))
(assert
 (= cbe382308_nested_multicall_completes cbe382308_nested_multicall_completes))
(assert
 (= cbe382308_outer_msg_value_nonzero cbe382308_outer_msg_value_nonzero))
(define-fun report_preconditions () Bool (and cbe382308_outer_msg_value_nonzero
     cbe382308_inner_multicall_nested_via_delegatecall
     cbe382308_inner_forwards_no_eth))
(define-fun report_safety () Bool (=> (and cbe382308_outer_msg_value_nonzero
         cbe382308_inner_multicall_nested_via_delegatecall
         cbe382308_inner_forwards_no_eth)
    cbe382308_nested_multicall_completes))
(define-fun report_effects () Bool cbe382308_integrations_broken)
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
(get-model)
