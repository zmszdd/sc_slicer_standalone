; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb93f34e5_add_rewards_unguarded () Bool)
(declare-fun cb93f34e5_claim_rewards_unguarded () Bool)
(declare-fun cb93f34e5_monetary_extraction_occurred () Bool)
(declare-fun cb93f34e5_reentry_window_exposed () Bool)
(assert
 (= cb93f34e5_add_rewards_unguarded cb93f34e5_add_rewards_unguarded))
(assert
 (= cb93f34e5_claim_rewards_unguarded cb93f34e5_claim_rewards_unguarded))
(assert
 (= cb93f34e5_monetary_extraction_occurred cb93f34e5_monetary_extraction_occurred))
(assert
 (= cb93f34e5_reentry_window_exposed cb93f34e5_reentry_window_exposed))
(define-fun report_preconditions () Bool (and cb93f34e5_add_rewards_unguarded cb93f34e5_claim_rewards_unguarded))
(define-fun report_safety () Bool (=> cb93f34e5_reentry_window_exposed (not cb93f34e5_reentry_window_exposed)))
(define-fun report_effects () Bool cb93f34e5_monetary_extraction_occurred)
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
