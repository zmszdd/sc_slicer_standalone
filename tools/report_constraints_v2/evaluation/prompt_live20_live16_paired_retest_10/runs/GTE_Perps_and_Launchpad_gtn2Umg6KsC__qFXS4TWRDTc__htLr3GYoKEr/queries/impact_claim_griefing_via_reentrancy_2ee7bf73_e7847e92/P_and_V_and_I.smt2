; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb22d87ea_add_rewards_unguarded () Bool)
(declare-fun cb22d87ea_claim_rewards_unguarded () Bool)
(declare-fun cb22d87ea_pending_accounting_increased () Bool)
(declare-fun cb22d87ea_reentrancy_window_usable_for_griefing () Bool)
(declare-fun cb22d87ea_reentrant_entrypoint_invoked () Bool)
(declare-fun cb22d87ea_transfer_from_completed () Bool)
(assert
 (= cb22d87ea_add_rewards_unguarded cb22d87ea_add_rewards_unguarded))
(assert
 (= cb22d87ea_claim_rewards_unguarded cb22d87ea_claim_rewards_unguarded))
(assert
 (= cb22d87ea_pending_accounting_increased cb22d87ea_pending_accounting_increased))
(assert
 (= cb22d87ea_reentrancy_window_usable_for_griefing cb22d87ea_reentrancy_window_usable_for_griefing))
(assert
 (= cb22d87ea_reentrant_entrypoint_invoked cb22d87ea_reentrant_entrypoint_invoked))
(assert
 (= cb22d87ea_transfer_from_completed cb22d87ea_transfer_from_completed))
(define-fun report_preconditions () Bool (and cb22d87ea_add_rewards_unguarded cb22d87ea_claim_rewards_unguarded))
(define-fun report_safety () Bool (=> (and cb22d87ea_pending_accounting_increased
         (not cb22d87ea_transfer_from_completed))
    (not cb22d87ea_reentrant_entrypoint_invoked)))
(define-fun report_effects () Bool cb22d87ea_reentrancy_window_usable_for_griefing)
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
(get-model)
