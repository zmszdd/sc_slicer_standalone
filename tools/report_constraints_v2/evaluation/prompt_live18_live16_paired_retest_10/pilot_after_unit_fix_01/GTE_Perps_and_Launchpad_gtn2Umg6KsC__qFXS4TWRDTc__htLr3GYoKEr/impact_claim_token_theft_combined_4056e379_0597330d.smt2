; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1a83c0d0_add_rewards_with_reentrant_token () Bool)
(declare-fun c1a83c0d0_no_reentrancy_guard_present () Bool)
(declare-fun c1a83c0d0_tokens_stolen_via_combined_weaknesses () Bool)
(declare-fun c1a83c0d0_transfer_ordered_before_bookkeeping () Bool)
(assert
 (= c1a83c0d0_add_rewards_with_reentrant_token c1a83c0d0_add_rewards_with_reentrant_token))
(assert
 (= c1a83c0d0_no_reentrancy_guard_present c1a83c0d0_no_reentrancy_guard_present))
(assert
 (= c1a83c0d0_tokens_stolen_via_combined_weaknesses c1a83c0d0_tokens_stolen_via_combined_weaknesses))
(assert
 (= c1a83c0d0_transfer_ordered_before_bookkeeping c1a83c0d0_transfer_ordered_before_bookkeeping))
(define-fun report_preconditions () Bool (and c1a83c0d0_add_rewards_with_reentrant_token
     c1a83c0d0_no_reentrancy_guard_present))
(define-fun report_safety () Bool (=> c1a83c0d0_tokens_stolen_via_combined_weaknesses
    (=> (and c1a83c0d0_add_rewards_with_reentrant_token
             c1a83c0d0_no_reentrancy_guard_present)
        c1a83c0d0_transfer_ordered_before_bookkeeping)))
(define-fun report_effects () Bool (and c1a83c0d0_tokens_stolen_via_combined_weaknesses
     c1a83c0d0_add_rewards_with_reentrant_token
     c1a83c0d0_no_reentrancy_guard_present
     (not c1a83c0d0_transfer_ordered_before_bookkeeping)))
