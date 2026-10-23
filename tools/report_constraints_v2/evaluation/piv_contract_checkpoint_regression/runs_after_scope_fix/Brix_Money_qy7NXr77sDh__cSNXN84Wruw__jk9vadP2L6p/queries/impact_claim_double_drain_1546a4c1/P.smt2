; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca494eb7a_custodian_is_contract_addr () Bool)
(declare-fun ca494eb7a_excess_drained_twice () Bool)
(declare-fun ca494eb7a_rebalance_callable_by_any_caller () Bool)
(declare-fun ca494eb7a_redemption_reduced_balance_before_rebalance () Bool)
(declare-fun ca494eb7a_vault_token_is_callback_enabled () Bool)
(assert
 (= ca494eb7a_custodian_is_contract_addr ca494eb7a_custodian_is_contract_addr))
(assert
 (= ca494eb7a_excess_drained_twice ca494eb7a_excess_drained_twice))
(assert
 (= ca494eb7a_rebalance_callable_by_any_caller ca494eb7a_rebalance_callable_by_any_caller))
(assert
 (= ca494eb7a_redemption_reduced_balance_before_rebalance ca494eb7a_redemption_reduced_balance_before_rebalance))
(assert
 (= ca494eb7a_vault_token_is_callback_enabled ca494eb7a_vault_token_is_callback_enabled))
(define-fun report_preconditions () Bool (and ca494eb7a_rebalance_callable_by_any_caller
     ca494eb7a_custodian_is_contract_addr
     ca494eb7a_vault_token_is_callback_enabled
     ca494eb7a_redemption_reduced_balance_before_rebalance))
(define-fun report_safety () Bool (=> (and ca494eb7a_rebalance_callable_by_any_caller
         ca494eb7a_custodian_is_contract_addr
         ca494eb7a_vault_token_is_callback_enabled
         ca494eb7a_redemption_reduced_balance_before_rebalance)
    (not ca494eb7a_excess_drained_twice)))
(define-fun report_effects () Bool (and ca494eb7a_rebalance_callable_by_any_caller
     ca494eb7a_custodian_is_contract_addr
     ca494eb7a_vault_token_is_callback_enabled
     ca494eb7a_redemption_reduced_balance_before_rebalance
     (not (not ca494eb7a_excess_drained_twice))))
(assert report_preconditions)
(check-sat)
(get-model)
