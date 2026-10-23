; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0a93815f_custodian_is_contract () Bool)
(declare-fun c0a93815f_rebalance_callable_by_any_caller () Bool)
(declare-fun c0a93815f_rebalance_lacks_reentrancy_guard () Bool)
(declare-fun c0a93815f_redemption_reduces_balance () Bool)
(declare-fun c0a93815f_token_is_callback_enabled () Bool)
(declare-fun c0a93815f_vault_undercollateralized () Bool)
(assert
 (= c0a93815f_custodian_is_contract c0a93815f_custodian_is_contract))
(assert
 (= c0a93815f_rebalance_callable_by_any_caller c0a93815f_rebalance_callable_by_any_caller))
(assert
 (= c0a93815f_rebalance_lacks_reentrancy_guard c0a93815f_rebalance_lacks_reentrancy_guard))
(assert
 (= c0a93815f_redemption_reduces_balance c0a93815f_redemption_reduces_balance))
(assert
 (= c0a93815f_token_is_callback_enabled c0a93815f_token_is_callback_enabled))
(assert
 (= c0a93815f_vault_undercollateralized c0a93815f_vault_undercollateralized))
(define-fun report_preconditions () Bool (and c0a93815f_rebalance_callable_by_any_caller
     c0a93815f_rebalance_lacks_reentrancy_guard
     c0a93815f_custodian_is_contract
     c0a93815f_token_is_callback_enabled))
(define-fun report_safety () Bool (=> (and c0a93815f_rebalance_callable_by_any_caller
         c0a93815f_redemption_reduces_balance)
    (not c0a93815f_vault_undercollateralized)))
(define-fun report_effects () Bool (and c0a93815f_rebalance_callable_by_any_caller
     c0a93815f_redemption_reduces_balance
     (not (not c0a93815f_vault_undercollateralized))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
