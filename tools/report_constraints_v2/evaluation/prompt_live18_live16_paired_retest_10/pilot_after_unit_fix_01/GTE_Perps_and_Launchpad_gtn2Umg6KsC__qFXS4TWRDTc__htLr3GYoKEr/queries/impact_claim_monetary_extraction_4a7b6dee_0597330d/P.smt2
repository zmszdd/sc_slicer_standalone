; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6674196f_add_rewards_invoked_with_reentrant_token () Bool)
(declare-fun c6674196f_monetary_extraction_occurred () Bool)
(declare-fun c6674196f_reentrancy_guard_absent () Bool)
(declare-fun c6674196f_transfer_from_completed_before_bookkeeping () Bool)
(assert
 (= c6674196f_add_rewards_invoked_with_reentrant_token c6674196f_add_rewards_invoked_with_reentrant_token))
(assert
 (= c6674196f_monetary_extraction_occurred c6674196f_monetary_extraction_occurred))
(assert
 (= c6674196f_reentrancy_guard_absent c6674196f_reentrancy_guard_absent))
(assert
 (= c6674196f_transfer_from_completed_before_bookkeeping c6674196f_transfer_from_completed_before_bookkeeping))
(define-fun report_preconditions () Bool (and c6674196f_add_rewards_invoked_with_reentrant_token
     c6674196f_reentrancy_guard_absent))
(define-fun report_safety () Bool (=> c6674196f_monetary_extraction_occurred
    (=> (and c6674196f_add_rewards_invoked_with_reentrant_token
             c6674196f_reentrancy_guard_absent)
        c6674196f_transfer_from_completed_before_bookkeeping)))
(define-fun report_effects () Bool (and c6674196f_monetary_extraction_occurred
     c6674196f_add_rewards_invoked_with_reentrant_token
     c6674196f_reentrancy_guard_absent
     (not c6674196f_transfer_from_completed_before_bookkeeping)))
(assert report_preconditions)
(check-sat)
(get-model)
