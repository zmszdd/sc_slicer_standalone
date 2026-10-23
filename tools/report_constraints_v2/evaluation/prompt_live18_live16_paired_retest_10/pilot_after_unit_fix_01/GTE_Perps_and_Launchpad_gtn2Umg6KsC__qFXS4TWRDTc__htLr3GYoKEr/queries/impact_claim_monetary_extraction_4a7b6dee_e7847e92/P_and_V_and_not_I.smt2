; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb93f34e5_add_rewards_with_reentrant_token () Bool)
(declare-fun cb93f34e5_claim_rewards_entered_in_window () Bool)
(declare-fun cb93f34e5_monetary_extraction_occurred () Bool)
(declare-fun cb93f34e5_no_reentrancy_guard_present () Bool)
(declare-fun cb93f34e5_pending_accounting_increased_before_transfer () Bool)
(assert
 (= cb93f34e5_add_rewards_with_reentrant_token cb93f34e5_add_rewards_with_reentrant_token))
(assert
 (= cb93f34e5_claim_rewards_entered_in_window cb93f34e5_claim_rewards_entered_in_window))
(assert
 (= cb93f34e5_monetary_extraction_occurred cb93f34e5_monetary_extraction_occurred))
(assert
 (= cb93f34e5_no_reentrancy_guard_present cb93f34e5_no_reentrancy_guard_present))
(assert
 (= cb93f34e5_pending_accounting_increased_before_transfer cb93f34e5_pending_accounting_increased_before_transfer))
(define-fun report_preconditions () Bool (and cb93f34e5_add_rewards_with_reentrant_token
     cb93f34e5_no_reentrancy_guard_present))
(define-fun report_safety () Bool (=> cb93f34e5_monetary_extraction_occurred
    (=> (and cb93f34e5_add_rewards_with_reentrant_token
             cb93f34e5_no_reentrancy_guard_present)
        (and (not cb93f34e5_pending_accounting_increased_before_transfer)
             (not cb93f34e5_claim_rewards_entered_in_window)))))
(define-fun report_effects () Bool (and cb93f34e5_monetary_extraction_occurred
     cb93f34e5_add_rewards_with_reentrant_token
     cb93f34e5_no_reentrancy_guard_present
     (not (and (not cb93f34e5_pending_accounting_increased_before_transfer)
               (not cb93f34e5_claim_rewards_entered_in_window)))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
