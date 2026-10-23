; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3da66a29_caller_is_authorized () Bool)
(declare-fun c3da66a29_custodian_is_contract () Bool)
(declare-fun c3da66a29_rebalance_invoked () Bool)
(declare-fun c3da66a29_reentrancy_guard_present () Bool)
(declare-fun c3da66a29_vault_undercollateralized_after_rebalance () Bool)
(assert
 (= c3da66a29_caller_is_authorized c3da66a29_caller_is_authorized))
(assert
 (= c3da66a29_custodian_is_contract c3da66a29_custodian_is_contract))
(assert
 (= c3da66a29_rebalance_invoked c3da66a29_rebalance_invoked))
(assert
 (= c3da66a29_reentrancy_guard_present c3da66a29_reentrancy_guard_present))
(assert
 (= c3da66a29_vault_undercollateralized_after_rebalance c3da66a29_vault_undercollateralized_after_rebalance))
(define-fun report_preconditions () Bool (and (not c3da66a29_caller_is_authorized)
     (not c3da66a29_reentrancy_guard_present)
     c3da66a29_custodian_is_contract))
(define-fun report_safety () Bool (=> (and c3da66a29_rebalance_invoked (not c3da66a29_caller_is_authorized))
    (not c3da66a29_vault_undercollateralized_after_rebalance)))
(define-fun report_effects () Bool (and c3da66a29_rebalance_invoked
     (not c3da66a29_caller_is_authorized)
     (not (not c3da66a29_vault_undercollateralized_after_rebalance))))
(assert report_preconditions)
(check-sat)
(get-model)
