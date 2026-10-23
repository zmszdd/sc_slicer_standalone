; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca494eb7a_callback_token_in_use () Bool)
(declare-fun ca494eb7a_custodian_is_contract () Bool)
(declare-fun ca494eb7a_excess_drained_twice () Bool)
(declare-fun ca494eb7a_reentrancy_guard_absent () Bool)
(assert
 (= ca494eb7a_callback_token_in_use ca494eb7a_callback_token_in_use))
(assert
 (= ca494eb7a_custodian_is_contract ca494eb7a_custodian_is_contract))
(assert
 (= ca494eb7a_excess_drained_twice ca494eb7a_excess_drained_twice))
(assert
 (= ca494eb7a_reentrancy_guard_absent ca494eb7a_reentrancy_guard_absent))
(define-fun report_preconditions () Bool (and ca494eb7a_reentrancy_guard_absent
     ca494eb7a_custodian_is_contract
     ca494eb7a_callback_token_in_use))
(define-fun report_safety () Bool (=> (and ca494eb7a_reentrancy_guard_absent
         ca494eb7a_custodian_is_contract
         ca494eb7a_callback_token_in_use)
    (not ca494eb7a_excess_drained_twice)))
(define-fun report_effects () Bool (and ca494eb7a_reentrancy_guard_absent
     ca494eb7a_custodian_is_contract
     ca494eb7a_callback_token_in_use
     (not (not ca494eb7a_excess_drained_twice))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
