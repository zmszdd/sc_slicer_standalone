; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb22d87ea_accounting_increased_before_transfer_from () Bool)
(declare-fun cb22d87ea_claim_rewards_reentered_during_transfer_from () Bool)
(declare-fun cb22d87ea_reentrancy_window_usable_for_griefing () Bool)
(declare-fun cb22d87ea_token_executes_code_during_transfer_from () Bool)
(assert
 (= cb22d87ea_accounting_increased_before_transfer_from cb22d87ea_accounting_increased_before_transfer_from))
(assert
 (= cb22d87ea_claim_rewards_reentered_during_transfer_from cb22d87ea_claim_rewards_reentered_during_transfer_from))
(assert
 (= cb22d87ea_reentrancy_window_usable_for_griefing cb22d87ea_reentrancy_window_usable_for_griefing))
(assert
 (= cb22d87ea_token_executes_code_during_transfer_from cb22d87ea_token_executes_code_during_transfer_from))
(define-fun report_preconditions () Bool cb22d87ea_token_executes_code_during_transfer_from)
(define-fun report_safety () Bool (=> (and cb22d87ea_claim_rewards_reentered_during_transfer_from
         cb22d87ea_reentrancy_window_usable_for_griefing)
    (=> (and cb22d87ea_token_executes_code_during_transfer_from
             cb22d87ea_accounting_increased_before_transfer_from)
        (not cb22d87ea_claim_rewards_reentered_during_transfer_from))))
(define-fun report_effects () Bool (and cb22d87ea_claim_rewards_reentered_during_transfer_from
     cb22d87ea_reentrancy_window_usable_for_griefing
     cb22d87ea_token_executes_code_during_transfer_from
     cb22d87ea_accounting_increased_before_transfer_from
     (not (not cb22d87ea_claim_rewards_reentered_during_transfer_from))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
