; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb93f34e5_accounting_increased_before_transfer_from () Bool)
(declare-fun cb93f34e5_monetary_extraction_occurred () Bool)
(declare-fun cb93f34e5_reentry_into_claim_rewards_during_transfer_from () Bool)
(declare-fun cb93f34e5_token_can_execute_code_during_transfer_from () Bool)
(assert
 (= cb93f34e5_accounting_increased_before_transfer_from cb93f34e5_accounting_increased_before_transfer_from))
(assert
 (= cb93f34e5_monetary_extraction_occurred cb93f34e5_monetary_extraction_occurred))
(assert
 (= cb93f34e5_reentry_into_claim_rewards_during_transfer_from cb93f34e5_reentry_into_claim_rewards_during_transfer_from))
(assert
 (= cb93f34e5_token_can_execute_code_during_transfer_from cb93f34e5_token_can_execute_code_during_transfer_from))
(define-fun report_preconditions () Bool cb93f34e5_token_can_execute_code_during_transfer_from)
(define-fun report_safety () Bool (=> (and cb93f34e5_reentry_into_claim_rewards_during_transfer_from
         cb93f34e5_monetary_extraction_occurred)
    (=> (and cb93f34e5_token_can_execute_code_during_transfer_from
             cb93f34e5_accounting_increased_before_transfer_from)
        (not cb93f34e5_reentry_into_claim_rewards_during_transfer_from))))
(define-fun report_effects () Bool (and cb93f34e5_reentry_into_claim_rewards_during_transfer_from
     cb93f34e5_monetary_extraction_occurred
     cb93f34e5_token_can_execute_code_during_transfer_from
     cb93f34e5_accounting_increased_before_transfer_from
     (not (not cb93f34e5_reentry_into_claim_rewards_during_transfer_from))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
