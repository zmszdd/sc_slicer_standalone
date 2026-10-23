; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c845b24bf_custodian_reenters_during_transfer () Bool)
(declare-fun c845b24bf_custodian_transfer_external_call () Bool)
(declare-fun c845b24bf_excess_drained_twice () Bool)
(declare-fun c845b24bf_rebalance_callable_by_any_caller () Bool)
(declare-fun c845b24bf_redemption_reduces_vault_balance () Bool)
(declare-fun c845b24bf_reentrancy_guard_absent () Bool)
(assert
 (= c845b24bf_custodian_reenters_during_transfer c845b24bf_custodian_reenters_during_transfer))
(assert
 (= c845b24bf_custodian_transfer_external_call c845b24bf_custodian_transfer_external_call))
(assert
 (= c845b24bf_excess_drained_twice c845b24bf_excess_drained_twice))
(assert
 (= c845b24bf_rebalance_callable_by_any_caller c845b24bf_rebalance_callable_by_any_caller))
(assert
 (= c845b24bf_redemption_reduces_vault_balance c845b24bf_redemption_reduces_vault_balance))
(assert
 (= c845b24bf_reentrancy_guard_absent c845b24bf_reentrancy_guard_absent))
(define-fun report_preconditions () Bool (and c845b24bf_rebalance_callable_by_any_caller
     c845b24bf_custodian_transfer_external_call
     c845b24bf_reentrancy_guard_absent
     c845b24bf_redemption_reduces_vault_balance))
(define-fun report_safety () Bool (=> (and c845b24bf_custodian_transfer_external_call
         c845b24bf_reentrancy_guard_absent)
    (and (not c845b24bf_custodian_reenters_during_transfer)
         (not c845b24bf_excess_drained_twice))))
(define-fun report_effects () Bool (and c845b24bf_custodian_transfer_external_call
     c845b24bf_reentrancy_guard_absent
     (not (and (not c845b24bf_custodian_reenters_during_transfer)
               (not c845b24bf_excess_drained_twice)))))
