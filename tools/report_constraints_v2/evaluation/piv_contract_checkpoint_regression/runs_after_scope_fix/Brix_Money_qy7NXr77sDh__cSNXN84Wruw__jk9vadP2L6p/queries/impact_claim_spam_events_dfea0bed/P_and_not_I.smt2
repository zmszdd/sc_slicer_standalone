; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ccb76e1ed_caller_is_authorized_rebalancer () Bool)
(declare-fun ccb76e1ed_rebalance_callable_by_any_caller () Bool)
(declare-fun ccb76e1ed_unauthorized_rebalance_occurred () Bool)
(declare-fun ccb76e1ed_vault_balance_reduced_by_redemption () Bool)
(assert
 (= ccb76e1ed_caller_is_authorized_rebalancer ccb76e1ed_caller_is_authorized_rebalancer))
(assert
 (= ccb76e1ed_rebalance_callable_by_any_caller ccb76e1ed_rebalance_callable_by_any_caller))
(assert
 (= ccb76e1ed_unauthorized_rebalance_occurred ccb76e1ed_unauthorized_rebalance_occurred))
(assert
 (= ccb76e1ed_vault_balance_reduced_by_redemption ccb76e1ed_vault_balance_reduced_by_redemption))
(define-fun report_preconditions () Bool (and ccb76e1ed_rebalance_callable_by_any_caller
     ccb76e1ed_vault_balance_reduced_by_redemption))
(define-fun report_safety () Bool (=> (and ccb76e1ed_rebalance_callable_by_any_caller
         ccb76e1ed_vault_balance_reduced_by_redemption)
    (or ccb76e1ed_caller_is_authorized_rebalancer
        (not ccb76e1ed_unauthorized_rebalance_occurred))))
(define-fun report_effects () Bool (and ccb76e1ed_rebalance_callable_by_any_caller
     ccb76e1ed_vault_balance_reduced_by_redemption
     (not (or ccb76e1ed_caller_is_authorized_rebalancer
              (not ccb76e1ed_unauthorized_rebalance_occurred)))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
