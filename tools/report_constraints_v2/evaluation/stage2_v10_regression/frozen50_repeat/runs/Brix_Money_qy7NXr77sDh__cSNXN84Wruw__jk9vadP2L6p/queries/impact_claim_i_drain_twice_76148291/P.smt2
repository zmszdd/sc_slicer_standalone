; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb5aada91_custodian_is_contract () Bool)
(declare-fun cb5aada91_excess_drained_twice () Bool)
(declare-fun cb5aada91_rebalance_callable_by_any_caller () Bool)
(declare-fun cb5aada91_reentrancy_guard_absent () Bool)
(declare-fun cb5aada91_token_callback_enabled () Bool)
(assert
 (= cb5aada91_custodian_is_contract cb5aada91_custodian_is_contract))
(assert
 (= cb5aada91_excess_drained_twice cb5aada91_excess_drained_twice))
(assert
 (= cb5aada91_rebalance_callable_by_any_caller cb5aada91_rebalance_callable_by_any_caller))
(assert
 (= cb5aada91_reentrancy_guard_absent cb5aada91_reentrancy_guard_absent))
(assert
 (= cb5aada91_token_callback_enabled cb5aada91_token_callback_enabled))
(define-fun report_preconditions () Bool (and cb5aada91_rebalance_callable_by_any_caller
     cb5aada91_reentrancy_guard_absent
     cb5aada91_custodian_is_contract
     cb5aada91_token_callback_enabled))
(define-fun report_safety () Bool (=> (and cb5aada91_rebalance_callable_by_any_caller
         cb5aada91_reentrancy_guard_absent
         cb5aada91_custodian_is_contract
         cb5aada91_token_callback_enabled)
    (not cb5aada91_excess_drained_twice)))
(define-fun report_effects () Bool (and cb5aada91_rebalance_callable_by_any_caller
     cb5aada91_reentrancy_guard_absent
     cb5aada91_custodian_is_contract
     cb5aada91_token_callback_enabled
     (not (not cb5aada91_excess_drained_twice))))
(assert report_preconditions)
(check-sat)
(get-model)
