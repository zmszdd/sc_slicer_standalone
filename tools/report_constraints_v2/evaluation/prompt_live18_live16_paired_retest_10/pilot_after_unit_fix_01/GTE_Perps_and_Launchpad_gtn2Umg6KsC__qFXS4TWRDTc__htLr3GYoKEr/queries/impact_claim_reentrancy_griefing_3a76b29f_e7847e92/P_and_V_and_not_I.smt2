; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6036c8e5_add_rewards_called () Bool)
(declare-fun c6036c8e5_claim_rewards_entered_in_window () Bool)
(declare-fun c6036c8e5_pending_accounting_increased_before_transfer () Bool)
(declare-fun c6036c8e5_reentrancy_guard_absent () Bool)
(declare-fun c6036c8e5_reentrancy_window_usable_for_griefing () Bool)
(declare-fun c6036c8e5_token_transferfrom_reentrant () Bool)
(assert
 (= c6036c8e5_add_rewards_called c6036c8e5_add_rewards_called))
(assert
 (= c6036c8e5_claim_rewards_entered_in_window c6036c8e5_claim_rewards_entered_in_window))
(assert
 (= c6036c8e5_pending_accounting_increased_before_transfer c6036c8e5_pending_accounting_increased_before_transfer))
(assert
 (= c6036c8e5_reentrancy_guard_absent c6036c8e5_reentrancy_guard_absent))
(assert
 (= c6036c8e5_reentrancy_window_usable_for_griefing c6036c8e5_reentrancy_window_usable_for_griefing))
(assert
 (= c6036c8e5_token_transferfrom_reentrant c6036c8e5_token_transferfrom_reentrant))
(define-fun report_preconditions () Bool (and c6036c8e5_add_rewards_called
     c6036c8e5_token_transferfrom_reentrant
     c6036c8e5_reentrancy_guard_absent))
(define-fun report_safety () Bool (=> (and c6036c8e5_pending_accounting_increased_before_transfer
         c6036c8e5_claim_rewards_entered_in_window
         c6036c8e5_reentrancy_window_usable_for_griefing)
    (=> (and c6036c8e5_add_rewards_called
             c6036c8e5_token_transferfrom_reentrant
             c6036c8e5_reentrancy_guard_absent)
        (not c6036c8e5_claim_rewards_entered_in_window))))
(define-fun report_effects () Bool (and c6036c8e5_pending_accounting_increased_before_transfer
     c6036c8e5_claim_rewards_entered_in_window
     c6036c8e5_reentrancy_window_usable_for_griefing
     c6036c8e5_add_rewards_called
     c6036c8e5_token_transferfrom_reentrant
     c6036c8e5_reentrancy_guard_absent
     (not (not c6036c8e5_claim_rewards_entered_in_window))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
