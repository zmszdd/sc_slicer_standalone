; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca494eb7a_custodian_is_contract () Bool)
(declare-fun ca494eb7a_excess_drained_twice () Bool)
(declare-fun ca494eb7a_rebalance_callable_by_any_caller () Bool)
(declare-fun ca494eb7a_reentrancy_guard_absent () Bool)
(declare-fun ca494eb7a_token_callback_enabled () Bool)
(assert
 (= ca494eb7a_custodian_is_contract ca494eb7a_custodian_is_contract))
(assert
 (= ca494eb7a_excess_drained_twice ca494eb7a_excess_drained_twice))
(assert
 (= ca494eb7a_rebalance_callable_by_any_caller ca494eb7a_rebalance_callable_by_any_caller))
(assert
 (= ca494eb7a_reentrancy_guard_absent ca494eb7a_reentrancy_guard_absent))
(assert
 (= ca494eb7a_token_callback_enabled ca494eb7a_token_callback_enabled))
(define-fun report_preconditions () Bool (and ca494eb7a_rebalance_callable_by_any_caller
     ca494eb7a_reentrancy_guard_absent
     ca494eb7a_custodian_is_contract
     ca494eb7a_token_callback_enabled))
(define-fun report_safety () Bool (=> (and ca494eb7a_rebalance_callable_by_any_caller
         ca494eb7a_reentrancy_guard_absent
         ca494eb7a_custodian_is_contract
         ca494eb7a_token_callback_enabled)
    (not ca494eb7a_excess_drained_twice)))
(define-fun report_effects () Bool (and ca494eb7a_rebalance_callable_by_any_caller
     ca494eb7a_reentrancy_guard_absent
     ca494eb7a_custodian_is_contract
     ca494eb7a_token_callback_enabled
     (not (not ca494eb7a_excess_drained_twice))))
(assert report_preconditions)
(check-sat)
(get-model)
