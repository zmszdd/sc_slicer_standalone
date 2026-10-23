; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4a7e9df3_add_rewards_invoked_with_reentrant_token () Bool)
(declare-fun c4a7e9df3_griefing_occurs () Bool)
(declare-fun c4a7e9df3_reentrancy_guard_absent () Bool)
(declare-fun c4a7e9df3_transfer_from_ordered_before_bookkeeping () Bool)
(assert
 (= c4a7e9df3_add_rewards_invoked_with_reentrant_token c4a7e9df3_add_rewards_invoked_with_reentrant_token))
(assert
 (= c4a7e9df3_griefing_occurs c4a7e9df3_griefing_occurs))
(assert
 (= c4a7e9df3_reentrancy_guard_absent c4a7e9df3_reentrancy_guard_absent))
(assert
 (= c4a7e9df3_transfer_from_ordered_before_bookkeeping c4a7e9df3_transfer_from_ordered_before_bookkeeping))
(define-fun report_preconditions () Bool (and c4a7e9df3_add_rewards_invoked_with_reentrant_token
     c4a7e9df3_reentrancy_guard_absent))
(define-fun report_safety () Bool (=> c4a7e9df3_griefing_occurs
    (=> (and c4a7e9df3_add_rewards_invoked_with_reentrant_token
             c4a7e9df3_reentrancy_guard_absent)
        c4a7e9df3_transfer_from_ordered_before_bookkeeping)))
(define-fun report_effects () Bool (and c4a7e9df3_griefing_occurs
     c4a7e9df3_add_rewards_invoked_with_reentrant_token
     c4a7e9df3_reentrancy_guard_absent
     (not c4a7e9df3_transfer_from_ordered_before_bookkeeping)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
